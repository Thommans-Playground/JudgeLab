# RunInfo

| Field | Value |
|---|---|
| Bounded Context | Reporting |
| DDD Type | Value Object |
| Aggregate | — |
| Ontology | `EvaluationRun` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `report.RunInfo` |
| Related | Input to: [Report](report.md) · References: Benchmark:Benchmark, Model Access:ModelConnector (target and judge) |

## Definition

What was run, with what, and when. It is Reporting's view of an evaluation run: just enough to write the report's metadata.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `benchmark` | `benchmark.Benchmark` | Value Object | yes | The benchmark that was run. |
| `rubric_id` | `str` | Value Object | yes | The rubric the judge used. |
| `target` | `connectors.ModelConnector` | Value Object | yes | Read only for `provider`, `model`, `base_url`. |
| `judge` | `connectors.ModelConnector` | Value Object | yes | Read only for `provider`, `model`, `base_url`. |
| `started_at` | `datetime` | Value Object | yes | UTC, from `report.utc_now()`. |
| `finished_at` | `datetime` | Value Object | yes | UTC, from `report.utc_now()`. |
| `run_id` | `str` | Value Object | yes | Defaults to `uuid.uuid4().hex`. |

## Behaviours (commands)

None. It is a frozen dataclass, built by `cli.run_command` after `evaluate()` returns. The helper `utc_now() -> datetime` supplies the times.

## Invariants

- Every run gets a fresh, unique `run_id` (AC-005-05, AC-005-07).
- Only the connectors' public identity is read. A connector's key is never reachable from RunInfo's report output (AC-005-06).

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **Evaluation:EvaluationRun**: the run itself. In v0.1 the run has no class, so its id and times live here. See the design note in [EvaluationRun](../evaluation/evaluation-run.md).

## Design note (candidate)

The run's identity is created in Reporting, which is backwards: Reporting should conform to Evaluation, not own part of it. Once an `EvaluationRun` class exists, RunInfo can be replaced by reading that object. The clock (`utc_now`) is a v0.2 `Clock` port candidate.
