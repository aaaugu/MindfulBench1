# MindCINS — construct-informed supervised training data and scripts

This **full-data RC4 package** contains MindCINS-4K (3,200 training / 800 validation) and MindCINS-6K (4,800 training / 1,200 validation), plus recovered QLoRA training scripts and configs. The 4K files are exact prefixes of the corresponding 6K files. Both reported model checkpoints were trained independently from the same Qwen2.5-7B-Instruct backbone, rather than continued from one another.

MindCINS is a supervised adaptation and trainability resource for the benchmark-defined five-process task, not an independently validated clinical counseling intervention. Trained checkpoint weights and the original provider API backend are not included. See `mindcins/DATA_CARD.md` and `docs/SOURCE_AND_LICENSE.md` for reuse boundaries.
