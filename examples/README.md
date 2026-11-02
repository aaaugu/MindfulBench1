# Synthetic code-check fixtures

These four short cases and responses were newly written solely to test file loading, prompt-building and deterministic scoring code. **They are not MindfulBench data, MindCINS supervision, source examples or real model outputs.** Their diagnostic labels and any mock Judge scores have no empirical meaning. Do not cite fixture outputs as experimental results.

From repository root:

```bash
python evaluation/scripts/build_judge_prompts.py --benchmark examples/synthetic_cases.jsonl --responses examples/synthetic_responses.jsonl --model synthetic-only --outdir /tmp/mindfulbench-smoke
```

The historical runner is NOT executed by this smoke test and requires an external model API. `scripts/verify_repository.py` checks the candidate's local file integrity without any external calls.
