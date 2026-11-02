# MindfulBench Data Card

## Summary

MindfulBench contains 720 Chinese multi-turn psychological-support dialogue cases designed for process-sensitive mindfulness-informed support evaluation.

| Split | Cases | Competing | Implicit | Minimal-contrast sides | Complete minimal pairs |
|---|---:|---:|---:|---:|---:|
| DEV | 180 | 60 | 60 | 60 | 30 |
| TEST | 540 | 180 | 180 | 180 | 90 |
| Total | 720 | 240 | 240 | 240 | 120 |

Each process has 36 DEV cases and 108 TEST cases.

## Process mapping

| Code | Process |
|---|---|
| S1 | Non-judgment |
| S2 | Allowing present experience |
| S3 | Allowing gradual change |
| S4 | Releasing state-contingent striving |
| S7 | Letting go of external outcomes |

## Exported fields (full-data RC4)

The current DEV180 and TEST540 draft files share a curated candidate schema: dialogue/structure fields, Gold strategy and Gold-card diagnostics, coarse `source_type`, and historical ID crosswalk fields. See `docs/SCHEMA.md`.

Raw source IDs, raw PsyQA records/provenance, authoring-risk notes beyond the released stance field, QC/audit logs, and internal closure metadata are not included.

## Held-out interpretation

TEST540 was held out during the reported study: it was not used for MindCINS authoring, training-recipe tuning, checkpoint selection, evaluator/rubric tuning, model-panel revision based on held-out results, or post-hoc repair. Its Gold is included in the full-data private staging candidate as a proposed post-evaluation release, subject to final release authorization and source terms. Future users should not tune on TEST540 Gold if they want a comparison analogous to the paper's held-out setting.

## Intended use

Suitable for research on process-sensitive response generation, diagnostic analysis, minimal-contrast behavior, and reproduction/extension of the reported evaluation protocol. It is not a clinical efficacy benchmark, therapist certification resource, diagnostic tool, or substitute for professional mental-health care.

## Language and domain

- Language: Chinese
- Format: multi-turn psychological-support dialogue
- Unit: one context requiring a next-turn response

## Source terms

This candidate omits raw source IDs/provenance. Potential future release does not constitute a blanket relicensing of any third-party source material.
