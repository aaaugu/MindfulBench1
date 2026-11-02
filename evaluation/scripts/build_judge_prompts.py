#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Core/Aux Judge prompt JSONL files from released MindfulBench data and model responses.
This is a reader-facing release utility. The system prompts and downstream historical runner/analyzer
are preserved separately as frozen historical artifacts.
"""
import argparse, json
from pathlib import Path

CORE_OUTPUT='{"primary_status": "GOLD_PRIMARY", "observed_primary_strategy": "S1", "secondary_strategies": [], "mechanism_grounded": true, "decisive_mechanism_addressed": true, "case_specificity": 2, "action_specificity": 2, "near_neighbor_discrimination": 2, "mindfulness_stance_integrity": 2, "generic_fallback": false, "mechanism_preserving_substitution": false, "substitution_severity": 0, "factual_consistency": true, "judge_score_before_cap": 8, "hard_cap": 10, "cap_reason": "", "mindfulness_core_score": 8, "evidence_span": "短片段", "action_span": "短片段", "brief_reason": "简洁理由"}'
AUX_OUTPUT='{"ra_score": 4, "nc_score": 4, "spb_status": "PASS", "ra_reason": "简洁理由", "nc_reason": "简洁理由", "spb_reason": "简洁理由"}'

def rows(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--benchmark',required=True)
    ap.add_argument('--responses',required=True,help='JSONL with {case_id,response}')
    ap.add_argument('--model',required=True,help='Display/model key used in aggregate output')
    ap.add_argument('--core-system',default=str(Path(__file__).resolve().parents[1]/'prompts'/'Core_System_v1_2_FROZEN_HISTORICAL.txt'))
    ap.add_argument('--aux-system',default=str(Path(__file__).resolve().parents[1]/'prompts'/'Aux_System_v1_2_FROZEN_HISTORICAL.txt'))
    ap.add_argument('--outdir',required=True)
    args=ap.parse_args()
    bench={r['case_id']:r for r in rows(args.benchmark)}
    responses=rows(args.responses)
    seen=set(); outdir=Path(args.outdir); outdir.mkdir(parents=True,exist_ok=True)
    core_sys=Path(args.core_system).read_text(encoding='utf-8').strip()
    aux_sys=Path(args.aux_system).read_text(encoding='utf-8').strip()
    core=[]; aux=[]; key=[]
    for i,rr in enumerate(responses,1):
        cid=rr.get('case_id'); resp=rr.get('response')
        if cid not in bench: raise ValueError(f'Unknown case_id: {cid}')
        if cid in seen: raise ValueError(f'Duplicate response for {cid}')
        if not isinstance(resp,str) or not resp.strip(): raise ValueError(f'Empty response for {cid}')
        seen.add(cid); b=bench[cid]; jid=f'MFBPUB-J{i:06d}'
        dialogue=f"用户：{b['user_1']}\n助手：{b['assistant_1']}\n用户：{b['user_2']}"
        gp=(f"gold_strategy: {b['gold_strategy']}\n"
            f"nearest_confusable: {b.get('nearest_confusable','')}\n"
            f"decisive_behavioral_evidence: {b.get('decisive_behavioral_evidence','')}\n"
            f"why_gold_over_neighbor: {b.get('why_gold_over_neighbor','')}\n"
            f"must_do: {b.get('must_do','')}\n"
            f"not_enough: {b.get('not_enough','')}\n"
            f"flip_condition: {b.get('flip_condition','')}")
        cp=(f"请对以下候选回复评分。\n\n[judge_id]\n{jid}\n\n[对话]\n{dialogue}\n\n"
            f"[候选回复]\n{resp.strip()}\n\n[Gold Card]\n{gp}\n\n请严格返回如下字段的 JSON：\n{CORE_OUTPUT}")
        aprompt=(f"请对以下候选回复评分。\n\n[judge_id]\n{jid}\n\n[对话]\n{dialogue}\n\n"
                 f"[候选回复]\n{resp.strip()}\n\n请严格返回如下字段的 JSON：\n{AUX_OUTPUT}")
        core.append({'judge_id':jid,'case_id':cid,'system_prompt':core_sys,'user_prompt':cp})
        aux.append({'judge_id':jid,'case_id':cid,'system_prompt':aux_sys,'user_prompt':aprompt})
        key.append({'judge_id':jid,'case_id':cid,'model':args.model,'subset':b['subset'],'pair_id':b.get('pair_id'),'gold_strategy':b['gold_strategy']})
    for name,data in [('core_prompts.jsonl',core),('aux_prompts.jsonl',aux),('answer_key.jsonl',key)]:
        (outdir/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in data),encoding='utf-8')
    print(f'Wrote {len(core)} cases to {outdir}')
if __name__=='__main__': main()
