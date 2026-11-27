# TestCase

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Modelled in | `Benchmark:TestCase` |
| Aliases | case, sample, prompt |
| Related | Belongs to: `Benchmark` · Sent to: `TargetModel` · Ends as: `CaseResult` (exactly 1 per run) |

## Definition

One question with the answer we expect. The question goes to the target model; the expected answer goes, with the target's actual answer, to the judge.

## Attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| id | text | Yes | Unique within its benchmark, e.g. `gk-001`. Identifies the case in progress lines and the report. |
| question | text | Yes | What the target model is asked. |
| expected_answer | text | Yes | The reference answer the judge compares against. Meaning matters, not wording. |

## Invariants

- `id`, `question` and `expected_answer` are all non-empty text; an error names the location, such as `cases[1].question` (AC-002-04).
- `id` is unique within its benchmark (AC-002-05).
- It has no other fields (AC-002-06).
- In a run, its question is sent to the target exactly once (AC-003-01).

## Examples

```json
{ "id": "gk-003", "question": "Who wrote the novel Pride and Prejudice?", "expected_answer": "Jane Austen" }
```

Edge case: a blank expected answer is rejected, because the judge would have nothing to compare against.

```json
{ "id": "gk-009", "question": "What is 2 + 2?", "expected_answer": "  " }
```

## Not to be confused with

- **CaseResult**: what happened to the test case in one run. The test case itself never changes.
- **The prompt sent to a model**: "prompt" is an alias people use for a test case, but the judge receives a different prompt built from the question, the expected answer and the actual answer.
- **Benchmark**: the whole collection, not one item of it.
