# MindCINS Data Card

## Summary

MindCINS is a Chinese multi-turn construct-informed supervised training resource for mindfulness-informed psychological-support dialogue.

| Resource | Train | Validation | Total |
|---|---:|---:|---:|
| MindCINS-4K | 3,200 | 800 | 4,000 |
| MindCINS-6K | 4,800 | 1,200 | 6,000 |

## Nesting

The full-data RC4 4K files are exact byte-preserved prefixes of their corresponding 6K files:

- `MindCINS_4K_train.jsonl` = first 3,200 physical rows of `MindCINS_6K_train.jsonl`
- `MindCINS_4K_valid.jsonl` = first 800 physical rows of `MindCINS_6K_valid.jsonl`

The 6K train and validation files have zero exact example overlap.

## Example structure

Each JSONL row has a single top-level field, `messages`, containing exactly four messages:

1. user
2. assistant
3. user
4. assistant

The final assistant message is the supervised target response.

## Public-export policy

This reader-facing release exposes only the model-visible SFT conversation content. It does not expose internal:
- case IDs;
- process/strategy labels;
- source IDs;
- donor/source provenance;
- authoring prompts;
- QC or blind-audit records;
- benchmark cases or Gold cards.

## Scope and limitations

The resource operationalizes a deliberately bounded set of mindfulness-informed dialogue processes used in the accompanying research. It should not be interpreted as a canonical or exhaustive taxonomy of mindfulness, psychotherapy, or mental-health support.

The data are intended for research and model development, not clinical deployment or evaluation of real-world treatment outcomes.
