# Evaluation details — RC4 full-data candidate

`data/MindfulBench_DEV180_public.jsonl` and `data/MindfulBench_TEST540_public.jsonl` contain the three-message dialogue context and the structured reference Gold fields. Response-generating models in the historical study received only the three dialogue messages (`user_1`, `assistant_1`, `user_2`), not the Gold annotations; the Core Judge received Gold only for scoring. The Auxiliary Judge did not receive Gold.

Refer to the original frozen protocol (`docs/MindBEN_EvaluationProtocol_v1_2_FROZEN_HISTORICAL.md`), `evaluation/prompts/`, and `evaluation/README.md` for the historical Core/Aux rubrics, JSON schemas and runner/analyzer. An actual compatible external API is needed for the Judge. Exact historical provider revisions and byte-identical re-execution are not established.

Both DEV and TEST Gold are present in this repository candidate. Evaluations conducted after public Gold exposure are not equivalent to the original sealed held-out study. The package includes only main-panel aggregate statistics, not complete original response or item-level Judge-output banks.
