# What this repository can and cannot reproduce

1. **Integrity:** SHA256 checks record exact byte content for the current candidate; `scripts/verify_repository.py` checks exported files.
2. **Benchmark structure:** with full-data files, local verification checks 180/540 case counts, three setting quotas, five process quotas, split uniqueness and intact matched pairs.
3. **Training resources:** with full-data files, local verification checks MindCINS sizes, strict 4K-in-6K prefix nesting, and disjoint train/validation records. Training scripts/configs are present but checkpoints, trained adapters and historical GPU runtime are not included.
4. **Evaluation:** Core/Aux system prompts, historical judge runner/analyzer and a current convenience prompt-building utility are included. The historical runner still requires API access, network and compatible provider behavior; frozen backend identity and deterministic identical scores cannot be promised. Convenience prompt construction is not certified byte-identical to every original historical prompt.
5. **Statistics:** reproducing exact paper tables without re-judging requires the original frozen model responses and judge outputs, which are not included in this candidate. The benchmark data plus scripts by themselves do not reconstruct historical model scores.
6. **Synthetic examples:** `examples/` is a code smoke test only. Mocked judge responses are not empirical evidence and must never appear as model-evaluation results.

**Historical scripts and prompts are retained byte-for-byte.** Any repairs should be separate new files, not edits to frozen evidence.
