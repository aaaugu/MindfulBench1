# MindCINS Public Schema

All four released files are JSONL. Each physical line is one JSON object.

## Schema

```json
{
  "messages": [
    {"role": "user", "content": "string"},
    {"role": "assistant", "content": "string"},
    {"role": "user", "content": "string"},
    {"role": "assistant", "content": "string"}
  ]
}
```

## Constraints verified for RC1

- exactly one top-level field: `messages`
- exactly four messages per row
- role order is always `user, assistant, user, assistant`
- message content is non-empty text
- no exact duplicate examples within the released 6K train file
- no exact duplicate examples within the released 6K validation file
- zero exact train–validation overlap
