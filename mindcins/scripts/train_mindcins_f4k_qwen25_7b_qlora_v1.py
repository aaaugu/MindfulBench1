#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from statistics import mean

import torch
import transformers
import peft
import accelerate
import bitsandbytes as bnb_lib
import datasets
import trl
import safetensors

from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    Trainer,
    TrainingArguments,
    set_seed,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
)

MODEL_DEFAULT = "Qwen/Qwen2.5-7B-Instruct"
SEED_DEFAULT = 20260921
TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if set(row.keys()) != {"messages"}:
                raise ValueError(
                    f"{path}:{i}: top-level keys must be exactly ['messages'], "
                    f"got {list(row.keys())}"
                )
            msgs = row["messages"]
            if not isinstance(msgs, list) or not msgs:
                raise ValueError(f"{path}:{i}: invalid messages")
            if msgs[-1].get("role") != "assistant":
                raise ValueError(f"{path}:{i}: last message must be assistant")
            rows.append(row)
    return rows


def encode_row(row, tokenizer, max_length, source, idx):
    messages = row["messages"]

    # Full conversation including final gold assistant response.
    full_ids = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=False,
    )

    # Context up to, but not including, the final assistant response.
    # add_generation_prompt=True includes the final assistant header.
    prefix_ids = tokenizer.apply_chat_template(
        messages[:-1],
        tokenize=True,
        add_generation_prompt=True,
    )

    if full_ids[:len(prefix_ids)] != prefix_ids:
        raise ValueError(
            f"{source}:{idx}: chat-template prefix mismatch; "
            "refusing ambiguous loss masking"
        )

    if len(full_ids) > max_length:
        raise ValueError(
            f"{source}:{idx}: sequence length {len(full_ids)} "
            f"exceeds frozen max_length={max_length}"
        )

    if len(prefix_ids) >= len(full_ids):
        raise ValueError(
            f"{source}:{idx}: no target assistant tokens after masking"
        )

    labels = [-100] * len(prefix_ids) + full_ids[len(prefix_ids):]

    return {
        "input_ids": full_ids,
        "attention_mask": [1] * len(full_ids),
        "labels": labels,
        "_seq_len": len(full_ids),
        "_target_tokens": len(full_ids) - len(prefix_ids),
        "_masked_tokens": len(prefix_ids),
    }


class EncodedDataset(Dataset):
    def __init__(self, rows):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        r = self.rows[idx]
        return {
            "input_ids": r["input_ids"],
            "attention_mask": r["attention_mask"],
            "labels": r["labels"],
        }


class CausalLMCollator:
    def __init__(self, pad_token_id):
        self.pad_token_id = pad_token_id

    def __call__(self, features):
        max_len = max(len(x["input_ids"]) for x in features)

        input_ids = []
        attention_mask = []
        labels = []

        for x in features:
            n = max_len - len(x["input_ids"])
            input_ids.append(
                x["input_ids"] + [self.pad_token_id] * n
            )
            attention_mask.append(
                x["attention_mask"] + [0] * n
            )
            labels.append(
                x["labels"] + [-100] * n
            )

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def print_token_stats(name, rows):
    seq = [x["_seq_len"] for x in rows]
    tgt = [x["_target_tokens"] for x in rows]
    masked = [x["_masked_tokens"] for x in rows]

    print(f"\n===== TOKEN STATS: {name} =====")
    print("n:", len(rows))
    print("seq_len min/mean/max:",
          min(seq), round(mean(seq), 2), max(seq))
    print("target_tokens min/mean/max:",
          min(tgt), round(mean(tgt), 2), max(tgt))
    print("masked_tokens min/mean/max:",
          min(masked), round(mean(masked), 2), max(masked))


def package_versions():
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "transformers": transformers.__version__,
        "peft": peft.__version__,
        "accelerate": accelerate.__version__,
        "bitsandbytes": bnb_lib.__version__,
        "datasets": datasets.__version__,
        "trl": trl.__version__,
        "safetensors": safetensors.__version__,
        "cuda_available": torch.cuda.is_available(),
        "bf16_supported": (
            torch.cuda.is_bf16_supported()
            if torch.cuda.is_available() else False
        ),
        "gpu": (
            torch.cuda.get_device_name(0)
            if torch.cuda.is_available() else None
        ),
    }


def write_sha256_manifest(output_dir, paths):
    out = Path(output_dir) / "SHA256SUMS.txt"
    lines = []
    for p in paths:
        p = Path(p)
        if p.exists() and p.is_file():
            lines.append(f"{sha256_file(p)}  {p}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("--train", required=True)
    ap.add_argument("--valid", required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--model", default=MODEL_DEFAULT)

    ap.add_argument("--max_length", type=int, default=1024)
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--grad_accum", type=int, default=8)

    ap.add_argument("--lora_r", type=int, default=16)
    ap.add_argument("--lora_alpha", type=int, default=32)
    ap.add_argument("--lora_dropout", type=float, default=0.05)

    ap.add_argument("--warmup_ratio", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=SEED_DEFAULT)

    ap.add_argument(
        "--sanity_only",
        action="store_true",
        help="Validate/tokenize dataset and exit before loading model.",
    )

    args = ap.parse_args()

    set_seed(args.seed)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("===== FINAL4K-SFT CONFIG =====")
    print("model:", args.model)
    print("train:", args.train)
    print("valid:", args.valid)
    print("output:", args.output_dir)
    print("max_length:", args.max_length)
    print("epochs:", args.epochs)
    print("lr:", args.lr)
    print("grad_accum:", args.grad_accum)
    print("LoRA r/alpha/dropout:",
          args.lora_r, args.lora_alpha, args.lora_dropout)
    print("warmup_ratio:", args.warmup_ratio)
    print("scheduler: cosine")
    print("optimizer: paged_adamw_8bit")
    print("seed:", args.seed)
    print("target_modules:", TARGET_MODULES)

    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        use_fast=True,
        trust_remote_code=True,
    )
    tokenizer.padding_side = "right"

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_raw = load_jsonl(args.train)
    valid_raw = load_jsonl(args.valid)

    if len(train_raw) != 3200:
        raise ValueError(f"Expected train=3200, got {len(train_raw)}")
    if len(valid_raw) != 800:
        raise ValueError(f"Expected valid=800, got {len(valid_raw)}")

    train_enc = [
        encode_row(r, tokenizer, args.max_length, args.train, i)
        for i, r in enumerate(train_raw, 1)
    ]
    valid_enc = [
        encode_row(r, tokenizer, args.max_length, args.valid, i)
        for i, r in enumerate(valid_raw, 1)
    ]

    print_token_stats("TRAIN", train_enc)
    print_token_stats("VALID", valid_enc)

    # Explicit masking sanity.
    total_target_train = sum(x["_target_tokens"] for x in train_enc)
    total_masked_train = sum(x["_masked_tokens"] for x in train_enc)

    print("\n===== LOSS MASK SANITY =====")
    print("train masked context tokens:", total_masked_train)
    print("train supervised final-assistant tokens:", total_target_train)
    print("all rows have supervised target:",
          all(x["_target_tokens"] > 0 for x in train_enc))
    print("loss policy: ONLY final assistant response is supervised")

    sanity_manifest = {
        "train_rows": len(train_raw),
        "valid_rows": len(valid_raw),
        "max_length": args.max_length,
        "seed": args.seed,
        "train_sha256": sha256_file(args.train),
        "valid_sha256": sha256_file(args.valid),
        "script_sha256": sha256_file(__file__),
        "target_modules": TARGET_MODULES,
        "loss_masking": "only_final_assistant_response",
        "token_stats": {
            "train_max_seq_len": max(x["_seq_len"] for x in train_enc),
            "valid_max_seq_len": max(x["_seq_len"] for x in valid_enc),
            "train_min_target_tokens": min(
                x["_target_tokens"] for x in train_enc
            ),
            "valid_min_target_tokens": min(
                x["_target_tokens"] for x in valid_enc
            ),
        },
    }

    (out / "dataset_sanity_manifest.json").write_text(
        json.dumps(sanity_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if args.sanity_only:
        print("\nSANITY_ONLY_PASS")
        return

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("Frozen recipe requires BF16 support")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=bnb_config,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        trust_remote_code=True,
    )

    model.config.use_cache = False

    model = prepare_model_for_kbit_training(
        model,
        use_gradient_checkpointing=True,
    )

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=TARGET_MODULES,
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    train_ds = EncodedDataset(train_enc)
    valid_ds = EncodedDataset(valid_enc)

    training_args = TrainingArguments(
        output_dir=args.output_dir,

        num_train_epochs=args.epochs,

        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.grad_accum,

        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=args.warmup_ratio,

        optim="paged_adamw_8bit",

        logging_strategy="steps",
        logging_steps=1,

        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=3,

        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,

        bf16=True,
        fp16=False,

        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},

        report_to=[],

        seed=args.seed,
        data_seed=args.seed,

        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=valid_ds,
        data_collator=CausalLMCollator(tokenizer.pad_token_id),
    )

    train_result = trainer.train()

    trainer.save_state()

    final_eval = trainer.evaluate()

    final_adapter = out / "final_adapter"
    trainer.model.save_pretrained(final_adapter)
    tokenizer.save_pretrained(final_adapter)

    (out / "loss_history.json").write_text(
        json.dumps(
            trainer.state.log_history,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (out / "training_arguments.json").write_text(
        json.dumps(
            training_args.to_dict(),
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    env = package_versions()
    try:
        env["nvidia_smi"] = subprocess.check_output(
            ["nvidia-smi"],
            text=True,
        )
    except Exception as e:
        env["nvidia_smi_error"] = repr(e)

    (out / "environment_manifest.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    run_manifest = {
        "model": args.model,
        "method": "QLoRA",
        "quantization": {
            "bits": 4,
            "type": "nf4",
            "double_quant": True,
            "compute_dtype": "bf16",
        },
        "train_rows": len(train_raw),
        "valid_rows": len(valid_raw),
        "epochs": args.epochs,
        "learning_rate": args.lr,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": args.grad_accum,
        "effective_batch_size": args.grad_accum,
        "scheduler": "cosine",
        "warmup_ratio": args.warmup_ratio,
        "optimizer": "paged_adamw_8bit",
        "max_length": args.max_length,
        "seed": args.seed,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "lora_dropout": args.lora_dropout,
        "target_modules": TARGET_MODULES,
        "loss_masking": "only_final_assistant_response",
        "best_model_checkpoint": trainer.state.best_model_checkpoint,
        "best_metric": trainer.state.best_metric,
        "train_metrics": train_result.metrics,
        "final_eval_metrics": final_eval,
        "train_sha256": sha256_file(args.train),
        "valid_sha256": sha256_file(args.valid),
        "script_sha256": sha256_file(__file__),
    }

    (out / "training_run_manifest.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    sha_paths = [
        args.train,
        args.valid,
        __file__,
        out / "dataset_sanity_manifest.json",
        out / "loss_history.json",
        out / "training_arguments.json",
        out / "environment_manifest.json",
        out / "training_run_manifest.json",
        out / "trainer_state.json",
        final_adapter / "adapter_config.json",
        final_adapter / "adapter_model.safetensors",
    ]

    write_sha256_manifest(out, sha_paths)

    print("\n" + "=" * 80)
    print("TRAINING COMPLETE")
    print("Best checkpoint:", trainer.state.best_model_checkpoint)
    print("Best eval loss:", trainer.state.best_metric)
    print("Final adapter:", final_adapter)
    print(json.dumps({
        "train_metrics": train_result.metrics,
        "final_eval_metrics": final_eval,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
