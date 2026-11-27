# Scorer

| Field | Value |
|---|---|
| Bounded Context | Evaluation |
| DDD Type | Domain Service |
| Aggregate | — |
| Ontology | `RunSummary` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `scoring.summarise` |
| Related | Reads: [CaseResult](case-result.md) · Produces: [RunSummary](run-summary.md) |

## Definition

The service that counts a run's outcomes into a RunSummary.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| — | — | — | — | Stateless. It is a module-level function. |

## Behaviours (commands)

- `summarise(results: Iterable[CaseResult]) -> Summary`: counts PASS, FAIL and ERROR and the total.

## Invariants

- It reads the results in a single pass, so a generator that can be read only once still works (AC-005-01).
- Every Outcome is counted in exactly one bucket.

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **RunSummary** (Evaluation): the value it returns.
- **Reporting:Report**: publishes the summary; it does not compute it.
