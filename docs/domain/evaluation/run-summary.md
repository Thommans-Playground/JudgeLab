# RunSummary

| Field | Value |
|---|---|
| Bounded Context | Evaluation |
| DDD Type | Value Object |
| Aggregate | — |
| Ontology | `RunSummary` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `scoring.Summary` |
| Related | Produced by: [Scorer](scorer.md) · Summarises: [EvaluationRun](evaluation-run.md) · Read by: Reporting:Report |

## Definition

The counts of a run's outcomes, with two derived metrics. Pass rate says how good the answers were, among those we could judge. Coverage says how much of the benchmark we could judge at all.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `total` | `int` | Value Object | yes | Number of case results. |
| `passed` | `int` | Value Object | yes | PASS count. |
| `failed` | `int` | Value Object | yes | FAIL count. |
| `errors` | `int` | Value Object | yes | ERROR count. |
| `evaluated` | `int` (property) | Value Object | — | `passed + failed`: cases with a verdict. |
| `pass_rate` | `float \| None` (property) | Value Object | — | `passed / evaluated`, or `None` when nothing was evaluated. |
| `coverage` | `float` (property) | Value Object | — | `evaluated / total`, or `0.0` when `total` is 0. |

## Behaviours (commands)

None. It is a frozen dataclass with derived properties.

## Invariants

- `total == passed + failed + errors`.
- `pass_rate` counts only cases with a verdict. Errors are never failures (AC-005-02).
- `pass_rate` is `None`, not 0, when no case reached a verdict (AC-005-02).
- `coverage` is the share of cases that reached a verdict (AC-005-03).

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **Reporting:Report**: the published document. It copies the summary's seven numbers under `"summary"`.
- **Scorer** (Evaluation): the service that builds a summary.
