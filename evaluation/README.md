# MindfulBench Evaluation Artifacts

This directory contains the candidate evaluation materials used to reconstruct the paper's automatic evaluation workflow.

## Contents

- `prompts/`: byte-preserved historical Core and Auxiliary system prompts. Stable strategy codes map to current paper-facing terminology via `../docs/TERMINOLOGY_MAPPING.md`.
- `scripts/build_judge_prompts.py`: release utility that combines a candidate benchmark split and model responses into Core/Aux prompt files plus an answer key.
- `scripts/run_judge_v1_1_FROZEN_HISTORICAL.py`: historical frozen judge runner. It contains the historical provider default, but endpoint/model can be overridden. No API key is included.
- `scripts/analyze_v1_1_FROZEN_HISTORICAL.py`: historical scoring/analyzer script implementing deterministic post-processing and aggregate metrics.
- `schemas/`: machine-readable JSON Schemas for benchmark cases and response submissions.
- `config/evaluation_config.json`: paper-facing record of the frozen Judge settings.

## Minimal local workflow

Prepare a response file such as:

```json
{"case_id":"MFB-TEST-0001","response":"..."}
```

Then build judge prompts:

```bash
python evaluation/scripts/build_judge_prompts.py \
  --benchmark data/MindfulBench_TEST540_public.jsonl \
  --responses responses.jsonl \
  --model my-model \
  --outdir eval_run
```

Run the Core and Auxiliary passes with the frozen historical runner (a compatible API endpoint and credentials are required):

```bash
python evaluation/scripts/run_judge_v1_1_FROZEN_HISTORICAL.py --input eval_run/core_prompts.jsonl --output eval_run/core_outputs.jsonl --resume
python evaluation/scripts/run_judge_v1_1_FROZEN_HISTORICAL.py --input eval_run/aux_prompts.jsonl --output eval_run/aux_outputs.jsonl --resume
```

Finally aggregate:

```bash
python evaluation/scripts/analyze_v1_1_FROZEN_HISTORICAL.py \
  --core eval_run/core_outputs.jsonl \
  --aux eval_run/aux_outputs.jsonl \
  --answer-key eval_run/answer_key.jsonl \
  --outdir eval_run/scored
```

TEST Gold is included in the **full-data private staging candidate** only. The code/metadata-only archive provides deliberately synthetic examples rather than frozen benchmark data; publication is not claimed. During the reported study, TEST540 was held out and was not used for training, tuning, checkpoint selection, evaluator/rubric tuning, or post-hoc repair.
