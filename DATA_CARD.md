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

## Held-out Interpretation

The TEST540 split was reserved for evaluation during the original study and was not used for MindCINS instance authoring, training-recipe tuning, checkpoint selection, or evaluator tuning before the main evaluation.

Following the original evaluation, the test-set Gold annotations were released publicly as part of the MindfulBench repository:

https://github.com/aaaugu/MindfulBench1

The publicly available TEST540 Gold labels support transparency, case-level inspection, and retrospective evaluation. However, future systems developed with access to these annotations cannot be considered evaluated under the same blind held-out conditions as the original study.

The release does not imply unrestricted redistribution rights for third-party source-derived materials.

## Intended use

Suitable for research on process-sensitive response generation, diagnostic analysis, minimal-contrast behavior, and reproduction/extension of the reported evaluation protocol. It is not a clinical efficacy benchmark, therapist certification resource, diagnostic tool, or substitute for professional mental-health care.

## Language and domain

- Language: Chinese
- Format: multi-turn psychological-support dialogue
- Unit: one context requiring a next-turn response

## Source terms

This candidate omits raw source IDs/provenance. Potential future release does not constitute a blanket relicensing of any third-party source material.
