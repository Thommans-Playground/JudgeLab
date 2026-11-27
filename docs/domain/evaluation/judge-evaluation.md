# JudgeEvaluation

| Field | Value |
|---|---|
| Bounded Context | Evaluation |
| DDD Type | Value Object |
| Aggregate | — |
| Ontology | `JudgeEvaluation` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `judge.JudgeEvaluation` |
| Related | Produced by: [Judge](judge.md) · Holds: [Verdict](verdict.md), Model Access:ModelResponse · References: [Rubric](rubric.md) (by id) · Held by: [CaseResult](case-result.md) |

## Definition

A validated verdict with its justification, the id of the rubric used, and the judge model's full response for identity and tracing. It exists only when the judge's reply was trustworthy.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `verdict` | `judge.Verdict` | Value Object | yes | PASS or FAIL. |
| `justification` | `str` | Value Object | yes | The judge's reason, trimmed and non-empty. |
| `rubric_id` | `str` | Value Object | yes | The rubric the judge applied. |
| `response` | `connectors.ModelResponse` | Value Object | yes | The judge call: served model, tokens, request id, latency. |

## Behaviours (commands)

None. It is a frozen dataclass built by `Judge.evaluate`.

## Invariants

- It is built only from a reply that passed `parse_verdict`: a JSON object with a supported verdict and a non-empty justification (AC-004-02).
- It records which judge model produced the verdict, through `response.served_model` (AC-004-04).
- It is never built from a refused, truncated or failed judge call. Those raise `JudgeError` (AC-004-03).

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **Verdict** (Evaluation): just PASS or FAIL. JudgeEvaluation adds the evidence.
- **CaseResult** (Evaluation): the whole case. It may hold a JudgeEvaluation.
- **Judge** (Evaluation): the service that produces it.
