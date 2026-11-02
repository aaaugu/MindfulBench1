#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MindBEN FormalDEV180 GLM analyzer v1.1
Structural fixes only relative to v1.0:
1) deduplicate resume history by judge_id, retaining successful parsed output;
2) unwrap provider structural wrappers:
   {"answer": {...}} or {"answer": "<JSON object string>"}.
No semantic re-judging and no rubric change.
"""
import argparse,json,statistics
from pathlib import Path
from collections import defaultdict

VALID_STRATS={"S0","S1","S2","S3","S4","S7"}

def load_jsonl(p):
    out=[]
    for n,line in enumerate(Path(p).read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try: out.append(json.loads(line))
        except Exception as e: print("BAD JSON",p,n,e)
    return out

def unwrap_answer(p):
    if isinstance(p,dict) and set(p.keys())=={"answer"}:
        a=p["answer"]
        if isinstance(a,dict):
            return a,True
        if isinstance(a,str):
            try:
                q=json.loads(a)
                if isinstance(q,dict): return q,True
            except Exception:
                pass
    return p,False

def successful_by_id(rows):
    done={}
    for r in rows:
        if r.get("status")=="ok" and isinstance(r.get("parsed"),dict):
            done[r.get("judge_id")]=r
    return done

def canon_core(p,gold):
    x=dict(p)
    obs=x.get("observed_primary_strategy")
    if obs not in VALID_STRATS: obs="S0"
    x["observed_primary_strategy"]=obs
    if obs=="S0": x["primary_status"]="NO_CLEAR_PRIMARY"
    elif obs==gold: x["primary_status"]="GOLD_PRIMARY"
    else: x["primary_status"]="NON_GOLD_PRIMARY"

    def clamp(name,lo,hi,default):
        try:v=int(x.get(name))
        except:v=default
        v=max(lo,min(hi,v)); x[name]=v; return v
    cs=clamp("case_specificity",0,2,0)
    ac=clamp("action_specificity",0,2,0)
    nn=clamp("near_neighbor_discrimination",0,2,0)
    st=clamp("mindfulness_stance_integrity",0,2,1)
    sev=clamp("substitution_severity",0,2,0)
    pre=clamp("judge_score_before_cap",1,10,1)

    for b in ("mechanism_grounded","decisive_mechanism_addressed","generic_fallback",
              "mechanism_preserving_substitution","factual_consistency"):
        x[b]=bool(x.get(b))
    if not x["mechanism_preserving_substitution"]:
        sev=0; x["substitution_severity"]=0
    elif sev==0:
        sev=1; x["substitution_severity"]=1

    cap=10; reasons=[]
    def apply(v,r):
        nonlocal cap
        cap=min(cap,v); reasons.append(r)
    if x["primary_status"]=="NON_GOLD_PRIMARY": apply(3,"NON_GOLD_PRIMARY")
    if x["primary_status"]=="NO_CLEAR_PRIMARY": apply(4,"NO_CLEAR_PRIMARY")
    if not x["factual_consistency"]: apply(4,"FACTUAL_INCONSISTENCY")
    if x["primary_status"]=="GOLD_PRIMARY" and (
        x["generic_fallback"] or ac==0 or not x["mechanism_grounded"] or not x["decisive_mechanism_addressed"]
    ): apply(5,"GOLD_BUT_GENERIC_OR_NO_ACTION_OR_NO_GROUNDING_OR_DECISIVE_MISSED")
    if x["mechanism_preserving_substitution"] and sev>=2: apply(5,"STRONG_MPS")
    elif x["mechanism_preserving_substitution"] and sev==1: apply(6,"PARTIAL_MPS")
    if ac==1 or cs<2: apply(6,"WEAK_ACTION_OR_PARTIAL_CASE_SPECIFICITY")
    if st==0: apply(6,"STANCE_0")
    if nn<2: apply(7,"LIMITED_NEAR_NEIGHBOR")
    if st==1: apply(7,"STANCE_1")
    x["hard_cap"]=cap
    x["cap_reason"]=";".join(dict.fromkeys(reasons))
    x["mindfulness_core_score"]=min(pre,cap)
    return x

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--core",required=True)
    ap.add_argument("--aux",default=None)
    ap.add_argument("--answer-key",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()

    key={r["judge_id"]:r for r in load_jsonl(args.answer_key)}
    raw=load_jsonl(args.core)
    good=successful_by_id(raw)
    outdir=Path(args.outdir); outdir.mkdir(parents=True,exist_ok=True)

    merged=[]; unwrap_n=0
    for jid,r in good.items():
        if jid not in key: continue
        p,u=unwrap_answer(r["parsed"]); unwrap_n+=int(u)
        meta=key[jid]
        c=canon_core(p,meta["gold_strategy"])
        merged.append({**meta,**c,"judge_id":jid,"structural_answer_unwrapped":u})

    (outdir/"core_merged_scored.jsonl").write_text(
        "".join(json.dumps(x,ensure_ascii=False)+"\n" for x in merged),encoding="utf-8"
    )

    summary={
        "physical_core_rows":len(raw),
        "unique_successful_core_judge_ids":len(good),
        "structural_answer_wrappers_normalized":unwrap_n,
        "models":{}
    }
    for m in sorted({r["model"] for r in merged}):
        rr=[r for r in merged if r["model"]==m]
        def rate(pred): return sum(pred(x) for x in rr)/len(rr)
        md={
            "n":len(rr),
            "MCS":round(statistics.mean(x["mindfulness_core_score"] for x in rr),4),
            "GPHR":round(rate(lambda x:x["primary_status"]=="GOLD_PRIMARY"),4),
            "GFR":round(rate(lambda x:x["generic_fallback"]),4),
            "MPSR":round(rate(lambda x:x["mechanism_preserving_substitution"]),4),
            "SVR":round(rate(lambda x:x["mindfulness_stance_integrity"]==0),4),
            "FIR":round(rate(lambda x:not x["factual_consistency"]),4),
        }
        for sub,name in [("competing","Competing_GPHR"),("minimal_contrast","Minimal_GPHR")]:
            z=[x for x in rr if x["subset"]==sub]
            md[name]=round(sum(x["primary_status"]=="GOLD_PRIMARY" for x in z)/len(z),4)
        pairs=defaultdict(list)
        for x in rr:
            if x["subset"]=="minimal_contrast" and x.get("pair_id"):
                pairs[x["pair_id"]].append(x)
        complete=[v for v in pairs.values() if len(v)==2]
        goodpairs=sum(all(x["primary_status"]=="GOLD_PRIMARY" and x["observed_primary_strategy"]==x["gold_strategy"] for x in p) for p in complete)
        md["minimal_pairs_n"]=len(complete)
        md["CPC"]=round(goodpairs/len(complete),4) if complete else None
        summary["models"][m]=md

    if args.aux:
        araw=load_jsonl(args.aux)
        agood=successful_by_id(araw)
        aux=[]; aux_unwrap=0
        for jid,r in agood.items():
            if jid not in key: continue
            p,u=unwrap_answer(r["parsed"]); aux_unwrap+=int(u)
            meta=key[jid]
            try: ra=max(1,min(5,int(p.get("ra_score"))))
            except: continue
            try: nc=max(1,min(5,int(p.get("nc_score"))))
            except: continue
            spb=str(p.get("spb_status","")).upper()
            if spb not in {"PASS","CAUTION","FAIL"}: continue
            aux.append({**meta,"judge_id":jid,"ra_score":ra,"nc_score":nc,"spb_status":spb,
                        "ra_reason":p.get("ra_reason",""),"nc_reason":p.get("nc_reason",""),
                        "spb_reason":p.get("spb_reason","")})
        (outdir/"aux_merged_scored.jsonl").write_text(
            "".join(json.dumps(x,ensure_ascii=False)+"\n" for x in aux),encoding="utf-8"
        )
        summary["physical_aux_rows"]=len(araw)
        summary["unique_successful_aux_judge_ids"]=len(agood)
        summary["aux_structural_answer_wrappers_normalized"]=aux_unwrap
        summary["aux_valid"]=len(aux)
        for m in sorted({x["model"] for x in aux}):
            z=[x for x in aux if x["model"]==m]
            summary["models"].setdefault(m,{})
            summary["models"][m]["RA"]=round(statistics.mean(x["ra_score"] for x in z),4)
            summary["models"][m]["NC"]=round(statistics.mean(x["nc_score"] for x in z),4)
            summary["models"][m]["SPB_CAUTION"]=round(sum(x["spb_status"]=="CAUTION" for x in z)/len(z),4)
            summary["models"][m]["SPB_FAIL"]=round(sum(x["spb_status"]=="FAIL" for x in z)/len(z),4)

    (outdir/"formaldev180_summary_v1_1.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8"
    )
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
