# MindfulBench + MindCINS — Full Research Resource (RC4)

This public repository provides the MindfulBench benchmark, structured Gold annotations, MindCINS training resources, evaluation scripts, and reported aggregate results.

Repository: https://github.com/aaaugu/MindfulBench1

The release includes 720 Chinese diagnostic cases (180 development and 540 test cases) and the MindCINS 4K/6K training and validation resources. The test-set Gold annotations were made publicly available after the original held-out evaluation. Consequently, future evaluations using these publicly accessible labels should not be considered equivalent to the original blind held-out evaluation.

No DOI or unrestricted reuse license is claimed. Third-party source-data permissions are described separately in the repository documentation.

MindfulBench is a 720-case Chinese, three-message, relation-conditioned diagnostic benchmark for mindfulness-informed psychological-support dialogue. Its benchmark-defined targets and functional criteria do not imply clinically optimal treatment or safe autonomous deployment.

## Files and sizes

| Path | Description |
|---|---|
| `data/MindfulBench_DEV180_public.jsonl` | 180 development cases, including structured Gold |
| `data/MindfulBench_TEST540_public.jsonl` | 540 historically held-out test cases, including structured Gold |
| `mindcins/data/MindCINS_4K_train.jsonl` | 3,200 training examples |
| `mindcins/data/MindCINS_4K_valid.jsonl` | 800 validation examples |
| `mindcins/data/MindCINS_6K_train.jsonl` | 4,800 training examples |
| `mindcins/data/MindCINS_6K_valid.jsonl` | 1,200 validation examples |
| `evaluation/` | Original Core/Aux evaluation prompts, scripts, schemas and configs |
| `mindcins/scripts/` | Recovered QLoRA training scripts |
| `results/` | Seven-system aggregates; original response/Judge banks not included |
| `docs/` | Scoring, schema, provenance and reproducibility notes |
| `examples/` | Clearly synthetic fixtures for testing scripts |

The 120 minimal-contrast pairs include 30 development and 90 test pairs. Each side of a pair shares its first two dialogue messages with its mate. The 4K MindCINS files are byte-for-byte prefixes of the corresponding 6K files.

## Quick integrity check

From the repository root:

```bash
python scripts/verify_repository.py
```

The check verifies included checksums, case counts, pair structure and training-file nesting; it does **not** independently establish clinical validity, source-data rights, or replay historical external API outputs.

## Historical evaluation and interpretation

The original held-out 540-case evaluation was completed before test Gold release. Publicly visible test Gold may be used for transparency and retrospective verification, but **future evaluations that could have seen these labels should not be presented as equally blind held-out tests**. The repository includes reported aggregates, not all original model response and item-level Judge-output banks, so aggregate files alone cannot independently reconstruct every published number.

## Origin, attribution, permissions

253 MindfulBench cases are source-grounded adaptations of PsyQA donor records; 467 cases are fresh. The official PsyQA repository specifies a signed user agreement for obtaining its full data. **Onward redistribution rights for adapted PsyQA-derived text have not been independently confirmed in this repository preparation.** Public visibility does not itself grant reuse or redistribution rights. See `docs/SOURCE_AND_LICENSE.md` for scope; no unrestricted open-data license is claimed here.

See `DATA_CARD.md`, `mindcins/DATA_CARD.md`, and `docs/REPRODUCIBILITY.md` for detailed limitations.

**Reference:** Sun et al. (2021), *PsyQA: A Chinese Dataset for Generating Long Counseling Text for Mental Health Support*, Findings of ACL-IJCNLP 2021.
