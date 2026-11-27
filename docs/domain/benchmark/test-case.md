# TestCase

| Field | Value |
|---|---|
| Bounded Context | Benchmark |
| DDD Type | Entity |
| Aggregate | Benchmark |
| Ontology | `TestCase` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `benchmark.TestCase` |
| Related | Owned by: [Benchmark](benchmark.md) · Referenced by: Evaluation:TargetResult, Evaluation:CaseResult |

## Definition

One question with the answer we expect. Its identity is its `id` within its benchmark, so two cases with the same text but different ids are different cases.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `id` | `str` | Identity | yes | Unique within the benchmark, such as `"c1"`. |
| `question` | `str` | Value Object | yes | Sent to the target model as the prompt. |
| `expected_answer` | `str` | Value Object | yes | Shown to the judge as the reference answer. |

## Behaviours (commands)

None. It is a frozen dataclass and changes only by reloading the benchmark.

## Invariants

- All three fields are non-empty strings (AC-002-04).
- No other fields are allowed (AC-002-06).
- `id` is unique within its benchmark (AC-002-05).

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **CaseResult** (Evaluation): what *happened* to a test case in one run. It carries the TestCase plus its outcome.
- **TargetResult** (Evaluation): the target's answer to one test case.

## Design note

The Python dataclass compares by value (all fields), not by `id` alone. In DDD terms it is an entity because the rest of the system tracks it by `id`: CaseResult and the report key on `case.id`. The class sets `__test__ = False` only so pytest does not collect it.
