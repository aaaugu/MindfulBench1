# 4K / 6K Nesting

The frozen authority package records MindCINS-4K as a byte-preserved subset of MindCINS-6K. This RC1 independently rechecked that relationship.

## Train

- 4K train rows: 3,200
- 6K train rows: 4,800
- 4K train is exactly the first 3,200 physical JSONL rows of 6K train: **PASS**
- frozen 4K train SHA256: `90172d995b808a60823ea51390c110b39f1d02eeb3221bc83494ad6cd921bd61`

## Validation

- 4K validation rows: 800
- 6K validation rows: 1,200
- 4K validation is exactly the first 800 physical JSONL rows of 6K validation: **PASS**
- frozen 4K validation SHA256: `4a0fcefe178ac4befd2573e7970e33ef5cd5da07e5904846ecf8a76ddafcf646`

## Split separation

- exact 6K train–validation example overlap: **0**
- 4K train examples appearing in 6K validation: **0**
- 4K validation examples appearing in 6K train: **0**

This nesting supports the reported nested supervision-budget comparison while keeping the frozen 4K examples fixed inside the 6K condition.
