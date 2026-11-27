# Verdict

| Field | Value |
|---|---|
| Bounded Context | Evaluation |
| DDD Type | Value Object |
| Aggregate | — |
| Ontology | `Verdict` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `judge.Verdict` |
| Related | Held by: [JudgeEvaluation](judge-evaluation.md) · Becomes: [Outcome](outcome.md) |

## Definition

The judge's decision on one answer: PASS (correct under the rubric) or FAIL (incorrect). There is no third value. "We don't know" is not a verdict.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `PASS` | `Verdict` (`StrEnum`, value `"PASS"`) | Value Object | — | The answer is acceptable. |
| `FAIL` | `Verdict` (`StrEnum`, value `"FAIL"`) | Value Object | — | The answer is not acceptable. |

## Behaviours (commands)

None. It is an enum.

## Invariants

- Only `PASS` or `FAIL` is accepted. `parse_verdict` trims and upper-cases the reply's value, and anything else raises `JudgeError` (AC-004-02).
- Each value has the same string as an Outcome, so `Outcome(verdict)` converts it.

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **Outcome** (Evaluation): the case's final state. It adds ERROR. A Verdict is what the judge said; an Outcome is what we conclude.
