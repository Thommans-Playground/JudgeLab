# TargetResult

| Field | Value |
|---|---|
| Bounded Context | Evaluation |
| DDD Type | Value Object |
| Aggregate | — |
| Ontology | `ModelResponse` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `runner.TargetResult` |
| Related | Holds: Benchmark:TestCase, Model Access:ModelResponse or Model Access:ConnectorError · Payload of: [CaseExecuted](case-executed.md) |

## Definition

What happened when one test case was sent to the target model: either a response or the connector error that prevented one. It is the first half of a case's journey, before judging.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `case` | `benchmark.TestCase` | Value Object | yes | The test case that was sent (or not sent). |
| `response` | `connectors.ModelResponse \| None` | Value Object | yes | The target's response, or `None` on error. |
| `error` | `connectors.ConnectorError \| None` | Value Object | yes | The failure, or `None` on success. |

## Behaviours (commands)

None. It is produced by `runner.run_target`.

## Invariants

- Exactly one of `response` and `error` is set.
- A case not sent because the run stopped has `response=None` and a plain `ConnectorError` whose message is `not sent: run stopped after <Error> on case <id>` (AC-003-03).
- Results come in benchmark order, one per case (AC-003-01).
- A connector error on one case does not stop later cases, unless it is auth or quota (AC-003-02, AC-003-03).

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | It is the payload of CaseExecuted, emitted by the run. | — |

## Not to be confused with

- **Model Access:ModelResponse**: the raw call result. TargetResult adds the case, and the error alternative.
- **CaseResult** (Evaluation): the final state, after judging.
