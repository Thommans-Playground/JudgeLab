# CaseExecuted

| Field | Value |
|---|---|
| Bounded Context | Evaluation |
| DDD Type | Domain Event |
| Ontology | `ModelResponse` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | The `on_target` callback of `runner.evaluate` (passed on as the `on_result` callback of `runner.run_target`); payload `runner.TargetResult` |

## Meaning

A test case was sent to the target model, and we now know what happened: it answered, refused, failed, or was not sent because the run had stopped.

## Emitted by

| Aggregate | Command | Condition |
|---|---|---|
| [EvaluationRun](evaluation-run.md) | `run_target(...)` / `evaluate(...)` | Once per test case, after its target step, including "not sent" cases. |

## Payload

| Field | Type | Description |
|---|---|---|
| `case` | `benchmark.TestCase` | The case. |
| `response` | `connectors.ModelResponse \| None` | The target's response, if any. |
| `error` | `connectors.ConnectorError \| None` | The failure, if any. |

## Consumers

| Consumer (context) | Reaction |
|---|---|
| Tests | Record each case id, to check every case is reported in order (AC-003-04). |
| Application layer (CLI) | None in v0.1. `cli.run_command` does not subscribe. |

## Guarantees

- In-process and synchronous: the callback runs inside the loop, before the next case is sent.
- Exactly once per test case, in benchmark order (AC-003-04).
- Inside `evaluate`, every CaseExecuted fires before the first CaseEvaluated, because all target calls finish before judging starts.
- An exception raised by the callback stops the run. There is no isolation.
- Naming note: the same callback is called `on_result` in `run_target` and `on_target` in `evaluate`.
