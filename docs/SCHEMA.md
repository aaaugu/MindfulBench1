# MindfulBench Candidate Export Schema — full-data RC4 private staging

Both `MindfulBench_DEV180_public.jsonl` and `MindfulBench_TEST540_public.jsonl` contain one JSON object per line and use the same candidate reader-facing schema. A machine-readable JSON Schema is available at `../evaluation/schemas/benchmark_case.schema.json`.

| Field | Type | Description |
|---|---|---|
| `case_id` | string | Neutral candidate case ID |
| `split` | string | `DEV` or `TEST` |
| `subset` | string | `implicit`, `competing`, or `minimal_contrast` |
| `pair_id` | string/null | Neutral candidate minimal-pair ID |
| `pair_role` | string/null | Side identifier for minimal pairs |
| `user_1` | string | First user turn |
| `assistant_1` | string | Existing assistant turn |
| `user_2` | string | Latest user turn to answer |
| `gold_strategy` | string | Stable process code (`S1`,`S2`,`S3`,`S4`,`S7`) |
| `nearest_confusable` | string/null | Prespecified neighboring process |
| `latent_control_rule` | string/null | Frozen functional-control description |
| `decisive_behavioral_evidence` | string/null | Case evidence supporting the target |
| `why_gold_over_neighbor` | string/null | Gold-over-neighbor rationale |
| `generic_fallback_trap` | string/null | Generic-response failure mode |
| `must_do` | string/null | Functional requirement for target realization |
| `not_enough` | string/null | Superficially supportive but insufficient pattern |
| `flip_condition` | string/null | Relation change under which the target should change |
| `stance_risk_note` | string/null | Mindfulness-stance implementation risk |
| `source_type` | string | `theory_anchored_fresh` or `real_source_adapted` |
| `legacy_case_id` | string | Historical internal case ID for provenance crosswalk |
| `legacy_pair_id` | string | Historical minimal-pair ID, present only for minimal pairs |

Raw source IDs/provenance and internal authoring/QC/closure metadata are not part of the curated candidate schema.
