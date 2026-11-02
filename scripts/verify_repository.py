#!/usr/bin/env python3
"""Check local RC4 content; no network or model API calls. Does NOT audit source permissions."""
import hashlib, json
from pathlib import Path
from collections import Counter, defaultdict

ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def read_jsonl(p):
    with p.open(encoding='utf-8') as h:
        return [json.loads(line) for line in h if line.strip()]

def check_checksums(p,root):
    checked=0
    for raw in p.read_text(encoding='utf-8').splitlines():
        if not raw.strip():continue
        digest,rel=raw.strip().split('  ',1)
        target=root/rel
        if not target.is_file(): raise AssertionError(f'Missing file: {target}')
        if sha(target)!=digest:raise AssertionError(f'Hash mismatch: {target}')
        checked+=1
    return checked

def run():
    n=check_checksums(ROOT/'SHA256SUMS.txt',ROOT)
    print(f'FILE_CHECKSUMS_OK: {n}')
    m=check_checksums(ROOT/'mindcins'/'SHA256SUMS.txt',ROOT/'mindcins')
    print(f'MINDCINS_CHECKSUMS_OK: {m}')
    f=ROOT/'data'/'MindfulBench_DEV180_public.jsonl'
    g=ROOT/'data'/'MindfulBench_TEST540_public.jsonl'
    if f.exists() and g.exists():
        allids=set()
        for name,p,number,nbpairs in [('DEV',f,180,30),('TEST',g,540,90)]:
            a=read_jsonl(p)
            assert len(a)==number,(name,len(a))
            ids=[x['case_id'] for x in a]
            assert len(ids)==len(set(ids))
            assert not allids.intersection(ids)
            allids.update(ids)
            assert Counter(x['subset'] for x in a)==Counter({'implicit':number//3,'competing':number//3,'minimal_contrast':number//3})
            assert Counter(x['gold_strategy'] for x in a)==dict.fromkeys(['S1','S2','S3','S4','S7'],number//5)
            pairs=defaultdict(list)
            for x in a:
                if x['subset']=='minimal_contrast':
                    assert x.get('pair_id')
                    pairs[x['pair_id']].append(x)
            assert len(pairs)==nbpairs
            assert all(len(v)==2 and len({x['case_id'] for x in v})==2 and len({x['gold_strategy'] for x in v})==2 for v in pairs.values())
            print(f'{name}_CASES_PAIRS_OK: {number} cases / {nbpairs} pairs')
    else:
        print('BENCHMARK_DATA: NOT PRESENT (code-only package)')
    t=ROOT/'mindcins'/'data'
    if (t/'MindCINS_4K_train.jsonl').exists():
        for split,n4,n6 in [('train',3200,4800),('valid',800,1200)]:
            four=(t/f'MindCINS_4K_{split}.jsonl').read_bytes().splitlines()
            six=(t/f'MindCINS_6K_{split}.jsonl').read_bytes().splitlines()
            assert len(four)==n4 and len(six)==n6
            assert four==six[:len(four)]
            print(f'MINDCINS_{split.upper()}_NESTING_OK: {n4}/{n6}')
        tr=set((t/'MindCINS_6K_train.jsonl').read_bytes().splitlines())
        va=set((t/'MindCINS_6K_valid.jsonl').read_bytes().splitlines())
        assert not tr.intersection(va)
    else:
        print('MINDCINS_DATA: NOT PRESENT (code-only package)')
    print('Local integrity checks passed; legal rights, privacy, and API backend are NOT certified.')

if __name__=='__main__':run()
