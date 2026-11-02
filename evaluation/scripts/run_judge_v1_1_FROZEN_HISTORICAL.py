#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MindBEN FormalDEV180 GLM-5.3-Flash judge runner — PARALLEL v1.1

Semantics are identical to v1.0:
- same endpoint/model
- temperature=0
- top_p=1
- reasoning_effort=low
- response_format=json_object
- transport retry only
- at most one structural-only JSON repair
- no semantic retry

Only change:
- independent judge items are submitted concurrently.

IMPORTANT:
Do NOT run this script at the same time as the old serial runner against the same output file.
Stop the old runner first (Ctrl+C), then use --resume on the same output file.

Example:
python .\run_formaldev180_glm53_judge_parallel_v1_1.py `
  --input .\MindBEN_FormalDEV180_CoreJudge_BasePilot360_Prompts_v1_0.jsonl `
  --output .\outputs\core360_basepilot_glm53_outputs.jsonl `
  --workers 6 `
  --resume
"""

import os, json, time, argparse, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

DEFAULT_ENDPOINT="https://api.commandcode.ai/provider/v1/chat/completions"
DEFAULT_MODEL="z-ai/glm-5.3-flash"

def get_key():
    for name in ("COMMAND_CODE_API_KEY","COMMANDCODE_API_KEY","CC_API_KEY"):
        v=os.getenv(name)
        if v:
            return v,name
    raise RuntimeError("请设置 COMMAND_CODE_API_KEY / COMMANDCODE_API_KEY / CC_API_KEY 之一")

def parse_json_obj(text):
    text=(text or "").strip()
    if text.startswith("```"):
        text=text.strip("`").strip()
        if text.lower().startswith("json"):
            text=text[4:].strip()
    try:
        x=json.loads(text)
        return x if isinstance(x,dict) else None
    except Exception:
        a=text.find("{"); b=text.rfind("}")
        if a>=0 and b>a:
            try:
                x=json.loads(text[a:b+1])
                return x if isinstance(x,dict) else None
            except Exception:
                return None
        return None

def call(endpoint,key,model,messages,max_tokens=1600,timeout=240):
    payload={
        "model":model,
        "messages":messages,
        "temperature":0,
        "top_p":1,
        "n":1,
        "stream":False,
        "max_tokens":max_tokens,
        "reasoning_effort":"low",
        "response_format":{"type":"json_object"},
    }
    r=requests.post(
        endpoint,
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
        json=payload,
        timeout=timeout
    )
    if r.status_code>=400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:1000]}")
    data=r.json()
    msg=(data.get("choices") or [{}])[0].get("message") or {}
    content=(msg.get("content") or "").strip()
    usage=data.get("usage") or {}
    return content,data.get("id"),usage

def load_success(path):
    done={}
    if not path.exists():
        return done
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r=json.loads(line)
        except Exception:
            continue
        if r.get("status")=="ok" and isinstance(r.get("parsed"),dict):
            done[r.get("judge_id")]=r
    return done

def run_one(p, endpoint, key, model):
    jid=p["judge_id"]
    waits=[2,4,8,16,24,32,45,60]
    last=None

    for attempt in range(8):
        try:
            raw,request_id,usage=call(
                endpoint,key,model,
                [{"role":"system","content":p["system_prompt"]},
                 {"role":"user","content":p["user_prompt"]}]
            )
            parsed=parse_json_obj(raw)
            structural_retry=False
            repair_raw=None

            if parsed is None:
                structural_retry=True
                repair_prompt=(
                    "上一条输出未通过 JSON 结构解析。不得改变任何语义判断或分数；"
                    "只把上一条内容修复为一个合法 JSON 对象，不要Markdown，不要新增解释。\n\n"
                    "上一条输出：\n"+raw
                )
                repair_raw,request_id2,usage2=call(
                    endpoint,key,model,
                    [{"role":"system","content":"你只做JSON结构修复，不改变原判断。"},
                     {"role":"user","content":repair_prompt}]
                )
                parsed=parse_json_obj(repair_raw)
                request_id=request_id2
                usage=usage2

            if parsed is None:
                return {
                    "judge_id":jid,
                    "case_id":p.get("case_id"),
                    "status":"invalid_json",
                    "parsed":None,
                    "raw":raw,
                    "repair_raw":repair_raw,
                    "structural_retry":structural_retry,
                    "error":"unresolved_after_one_structural_retry",
                    "request_id":request_id,
                    "usage":usage,
                }

            return {
                "judge_id":jid,
                "case_id":p.get("case_id"),
                "status":"ok",
                "parsed":parsed,
                "raw":raw,
                "repair_raw":repair_raw,
                "structural_retry":structural_retry,
                "error":None,
                "request_id":request_id,
                "usage":usage,
            }

        except Exception as e:
            last=repr(e)
            if attempt<7:
                time.sleep(waits[attempt])

    return {
        "judge_id":jid,
        "case_id":p.get("case_id"),
        "status":"transport_error",
        "parsed":None,
        "raw":None,
        "repair_raw":None,
        "structural_retry":False,
        "error":last,
        "request_id":None,
        "usage":{},
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--endpoint",default=os.getenv("COMMAND_CODE_BASE_URL",DEFAULT_ENDPOINT))
    ap.add_argument("--model",default=os.getenv("COMMAND_CODE_MODEL",DEFAULT_MODEL))
    ap.add_argument("--workers",type=int,default=6)
    ap.add_argument("--resume",action="store_true")
    args=ap.parse_args()

    if args.workers < 1:
        raise ValueError("--workers must be >=1")
    if args.workers > 12:
        print("WARNING: workers > 12 may trigger provider rate limits.")

    prompts=[json.loads(x) for x in Path(args.input).read_text(encoding="utf-8").splitlines() if x.strip()]
    key,key_name=get_key()
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)

    done=load_success(out) if args.resume else {}
    todo=[p for p in prompts if p["judge_id"] not in done]

    print("model:",args.model)
    print("key env:",key_name)
    print("prompts total:",len(prompts))
    print("resume successful:",len(done))
    print("remaining:",len(todo))
    print("workers:",args.workers)

    mode="a" if args.resume else "w"
    completed=0
    status_counts={}

    with out.open(mode,encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            fut2p={ex.submit(run_one,p,args.endpoint,key,args.model):p for p in todo}
            for fut in as_completed(fut2p):
                p=fut2p[fut]
                completed+=1
                try:
                    rec=fut.result()
                except Exception as e:
                    rec={
                        "judge_id":p["judge_id"],
                        "case_id":p.get("case_id"),
                        "status":"worker_exception",
                        "parsed":None,
                        "raw":None,
                        "repair_raw":None,
                        "structural_retry":False,
                        "error":repr(e),
                        "request_id":None,
                        "usage":{},
                    }

                f.write(json.dumps(rec,ensure_ascii=False)+"\n")
                f.flush()

                st=rec.get("status")
                status_counts[st]=status_counts.get(st,0)+1
                print(
                    f"[{completed}/{len(todo)}] {rec['judge_id']} "
                    f"{st} | running_counts={status_counts}"
                )

    final_done=load_success(out)
    print("="*80)
    print("FINISHED:",out)
    print("unique successful judge_id:",len(final_done),"/",len(prompts))
    print("If < total, rerun the exact same command with --resume.")

if __name__=="__main__":
    main()
