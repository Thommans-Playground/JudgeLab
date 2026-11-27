# CaseEvaluated

| Field | Value |
|---|---|
| Bounded Context | Evaluation |
| DDD Type | Domain Event |
| Ontology | `CaseResult` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | The `on_result` callback of `runner.evaluate`; payload `scoring.CaseResult` |

## Meaning

A test case reached its final Outcome (PASS, FAIL or ERROR) in this run.

## Emitted by

| Aggregate | Command | Condition |
|---|---|---|
| [EvaluationRun](evaluation-run.md) | `evaluate(...)` | Once per test case, right after its CaseResult is built. |

## Payload

| Field | Type | Description |
|---|---|---|
| `case` | `benchmark.TestCase` | The case. |
| `outcome` | `scoring.Outcome` | PASS, FAIL or ERROR. |
| `target` | `connectors.ModelResponse \| None` | The target's response. |
| `judgement` | `judge.JudgeEvaluation \| None` | The verdict and evidence, for PASS or FAIL. |
| `error_stage` | `str \| None` | `"target"` or `"judge"`, for ERROR. |
| `error` | `str \| None` | The error message, for ERROR. |

## Consumers

| Consumer (context) | Reaction |
|---|---|
| Application layer (CLI) | `show_progress` prints `[n/total] <case id>: <outcome>`, plus `(<stage>: <error>)` for an ERROR. |

## Guarantees

- In-process and synchronous: the callback runs before the next case is judged.
- Exactly once per test case, in benchmark order.
- The payload is immutable (a frozen dataclass), so a consumer cannot change the run's results.
- An exception raised by the callback stops the run. There is no isolation.
