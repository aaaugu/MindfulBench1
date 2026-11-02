# Generation Configuration Used in the Reported Study

This file records the paper-facing generation setup. Gold information, process labels, Judge rubrics, and comparison information were withheld from generation during the reported study.

## Shared model-visible instruction

System:

```text
你正在进行一段心理支持对话。
```

User template:

```text
已有对话：
用户：{user_1}
助手：{assistant_1}
用户：{user_2}
请根据已有对话，生成自然、有帮助的下一轮回复。
请直接回复用户，不要解释你的分析过程。
建议长度为80–150个汉字。
```

The suggested length is a soft instruction rather than a post-hoc truncation rule.

## Local Qwen-family generation

Used for Qwen2.5-7B-Instruct, MindCINS-4K, and MindCINS-6K:

```text
do_sample = true
temperature = 0.2
top_p = 0.9
max_new_tokens = 256
repetition_penalty = 1.0
seed = 20260921 + zero-based input index
```

InternLM2.5-7B-Chat and MindChat-Qwen-7B-v2 used their native chat interfaces with the same decoding values and per-case seed rule.

## API generation

DeepSeek V4 Flash and Qwen3.8 Flash were evaluated through a DashScope OpenAI-compatible chat-completions interface with:

```text
temperature = 0.2
top_p = 0.9
max_tokens = 1200
stream = false
enable_thinking = true
```

Neither `seed` nor `repetition_penalty` was sent to these API models. The study therefore uses harmonized task instructions rather than claiming identical decoding conditions across providers.

## Retry rule

Retries were permitted only for execution failures (e.g., network/HTTP failure, timeout, OOM/runtime failure, or completely empty/unusable output). Response quality was never a retry criterion. For each case/model, the first successful non-empty response was retained and not regenerated.
