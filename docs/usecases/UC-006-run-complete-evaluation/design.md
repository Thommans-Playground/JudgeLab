# UC-006 Design: Run complete evaluation

> **Draft for review.** Design says *how* the code realises the [analysis](analysis.md): real classes, signatures, patterns and where they sit in the [hexagonal architecture](../../design.md). It describes the reference solution the codealongs build.

| Field | Value |
|---|---|
| Use case | [UC-006](README.md) |
| Slices | [T-006-01](T-006-01-cli-and-orchestration.md) (CLI and orchestration), [T-006-02](T-006-02-live-end-to-end-benchmark.md) (live end-to-end benchmark) |
| Code | `judgelab.cli` (driving adapter, composition root), `judgelab.config`, calling `judgelab.runner`, `judgelab.scoring`, `judgelab.report` |
| Decisions | [ADR-001](../../decisions/ADR-001.md) (hexagonal), [ADR-002](../../decisions/ADR-002.md) (diagrams, as-built check) |

## 1. From analysis to design

| Analysis class | Design element | Hexagon role |
|---|---|---|
| Command Line (boundary) | `cli.main(argv=None, *, connector_factory=create_connector) -> int`, with `argparse`; the `judgelab` console script | Driving adapter, composition root |
| Config File (boundary) | `config.load_config(path) -> EvaluationConfig` (YAML, `yaml.safe_load`) | Driving-side adapter (YAML) |
| Model Interface (boundary) | `ModelConnector` port, built by `connector_factory(profile)`, which defaults to `connectors.create_connector` | Driven port + adapters |
| Report Store (boundary) | `report.write_report(report, directory) -> Path` | Edge I/O, no port in v0.1 |
| Run Evaluation (control) | `cli.run_command(config_path, output_dir, connector_factory) -> int` | Application service |
| Evaluation Config (entity) | `config.EvaluationConfig` (frozen dataclass) | Application layer |
| Connection Profile (entity) | `connectors.ConnectionProfile` | Core value object (Model Access) |
| Benchmark (entity) | `benchmark.Benchmark`, from `load_benchmark(config.dataset)` | Core aggregate (Benchmark) |
| Rubric (entity) | `judge.Rubric`, from `get_rubric(config.rubric)` | Core value object (Evaluation) |
| Evaluation Run (entity) | the `list[CaseResult]` from `runner.evaluate()`, plus `report.RunInfo` with times from `report.utc_now()` | Core (implicit aggregate) |
| Case Result (entity) | `scoring.CaseResult`; each one is passed to `on_result` as the CaseEvaluated event | Core entity (Evaluation) |
| Run Summary (entity) | `scoring.Summary`, from `summarise(results)`, printed by `cli.print_summary()` | Core value object (Evaluation) |

The **Evaluation Run** has no class in v0.1. It is implicit: `runner.evaluate()` returns a `list[CaseResult]`, and `run_command` keeps the run's identity and times in `RunInfo` (see [Evaluation](../../domain/evaluation/README.md)). The two meet only when `run_command` passes both to `build_report`.

The **CaseEvaluated** domain event is the `on_result: Callable[[CaseResult], None]` callback of `runner.evaluate`. `run_command` passes its local closure `show_progress`, which counts the cases done and prints `[done/total] id: OUTCOME`, plus `  (stage: message)` for an ERROR. The CaseExecuted event (`on_target`) exists in `evaluate`, but the CLI doesn't subscribe to it.

## 2. Design classes

Diagram: [UC-006 design classes](diagrams/design-classes.puml)

## 3. Design sequences

**Main success scenario.** One command, five cases, one report, exit code 0. Each CaseEvaluated event drives a progress line:

Diagram: [UC-006 design sequence](diagrams/design-sequence.puml)

**Extensions 1a and 1c.** The run cannot start. Every setup error is caught in one place, printed as `error: ...` and turned into exit code 1, before any model is called or any report is written:

Diagram: [UC-006 design sequence, startup error](diagrams/design-sequence-startup-error.puml)

**Composition root.** How `main` wires the connector factory, the profiles and the `Judge`, and how a test swaps in fakes through the same parameter:

Diagram: [UC-006 design sequence, composition root](diagrams/design-sequence-composition.puml)

Extensions 3a, 3b and 4a happen inside `runner.evaluate` and are drawn in [UC-003](../UC-003-execute-target-model/design.md) and [UC-004](../UC-004-evaluate-responses/design.md). Extension 7a is drawn in [UC-005](../UC-005-generate-report/design.md). Extension 1b is the expression `output_dir or config.output_dir`.

## 4. Patterns and principles

| Pattern / principle | Where | Why |
|---|---|---|
| Ports and adapters | `run_command` reaches models only through `ModelConnector`; `config` and `cli` are adapters on the driving side | The core never sees argparse, YAML or an SDK ([ADR-001](../../decisions/ADR-001.md)) |
| Composition root | `run_command` is the one place that creates connectors, the `Judge` and `RunInfo` | Every other module receives its collaborators; nothing else chooses an adapter |
| Dependency injection | `main(..., connector_factory=create_connector)` passes the factory down to `run_command` | Tests pass a `fake_factory` returning `FakeConnector`, so the whole CLI runs with no network and no keys (AC-006-05 to AC-006-07) |
| Factory Method / Registry | `create_connector(profile)` looks up `CONNECTORS[profile.provider]` | A provider is chosen by configuration, so swapping target and judge needs no code (AC-006-11) |
| Observer (lightweight) | `on_result=show_progress`, the CaseEvaluated event | The runner reports progress without knowing about printing |
| Fail fast at the edge | all of setup sits in one `try` before `evaluate` is called; connectors read their key in `__init__` | A bad config, rubric, dataset or missing key costs nothing (AC-006-06) |
| Errors as values at the edge | `except (ConfigError, ProfileError, BenchmarkError, JudgeError, ConnectorError)` prints `error: {e}` and returns 1 | One line, no traceback; error messages are written never to include a key's value |
| Exit codes as the contract | `main` returns 0 or 1; argparse exits 2 | Scripts and CI can tell "ran" from "couldn't start" from "used wrongly" |

## 5. Rules from the analysis, and where the design keeps them

| Rule | Kept by |
|---|---|
| Setup errors before the first call, `error:` and exit 1 | `run_command`'s `try` covers `load_config`, `load_benchmark`, `get_rubric` and both `connector_factory` calls; `read_secret` raises `ConnectorAuthError` from the connector's `__init__`; `load_config` re-raises a `ProfileError` (unknown setting, pasted key) as `ConfigError` with `from None` |
| Missing `--config` is exit 2 | `run.add_argument("--config", type=Path, required=True)`: argparse prints usage and raises `SystemExit(2)` |
| Config names everything; `--output-dir` overrides | `EvaluationConfig(target, judge, dataset, rubric, output_dir)`, with `output.dir` defaulting to `"reports"`; `write_report(..., output_dir or config.output_dir)` |
| The verdict is the outcome | `runner._judge` returns `CaseResult(case, Outcome(judgement.verdict), response, judgement)` |
| An untrusted answer is not judged | `runner._judge` returns ERROR at stage `"target"` for a `TargetResult.error` or a truncated response, before calling `Judge.evaluate` |
| Judge failure is ERROR; stop after auth or quota | `runner._judge` catches `JudgeError`; `evaluate` sets `judge_stopped_by` when the cause is in `STOP_THE_RUN` |
| A refusal is judged | `runner._judge` sends `f"[refused] {response.refusal}"` as the actual answer |
| Progress, then totals and report path | `show_progress` (CaseEvaluated), then `print_summary(summary)` and `print(f"Report: {path}")` |
| Exit 0 means completed | `run_command` returns 0 after writing the report, whatever the outcomes |
| Swap is configuration only | the CLI builds both connectors from profiles through the same factory; `runner` and `Judge` see only `ModelConnector` |

## 6. Design notes and candidate refactorings

- **EvaluationRun aggregate.** The run is implicit: a `list[CaseResult]` plus `RunInfo`, held together only by local variables in `run_command`. An `EvaluationRun` class would own the run id and times, the stop-judging policy that now lives in `runner.evaluate`, the invariant "one CaseResult per TestCase", and its `Summary`. It would also raise the CaseEvaluated event itself. This is the main candidate refactoring of v0.1.
- **Two phases, not one loop per case.** `runner.evaluate` iterates over the `list` returned by `run_target`, so every target call finishes before the first judge call, and no progress line appears until the target stage is over. The use case's steps 3 to 5 read as one case at a time. No rule depends on the order, but a long benchmark looks stalled. Making `run_target` a generator (or printing on `on_target`) would interleave the stages.
- **Only setup errors are caught.** An exception during the run or while writing the report (for example an `OSError` from `write_report`, or a bug in an adapter that breaks the "only ConnectorError escapes" contract) ends in a traceback and no report. Catching `OSError` around `write_report` with an `error:` line, and a distinct exit code, would keep the CLI's one-line promise.
- **`print_summary` drops the coverage in the n/a branch.** With no verdicts, it prints "Pass rate: n/a (no case reached a verdict)" alone, as extension 7a says, but UC-005's rule "the pass rate is always shown next to the error count and the coverage" is kept only by the error count on the line above (the coverage would be 0.0%).
- **`run_command` does several jobs**: composition, orchestration and presentation (printing). Splitting a `run_evaluation(config, connectors) -> (RunInfo, results, summary)` service from the printing would give UC-006 an application service that is testable without capturing stdout.
- **Edge I/O without ports.** `load_benchmark`, `write_report`, `utc_now` and `read_secret` are plain functions called directly. By the rule in [ADR-001](../../decisions/ADR-001.md), they become ports (BenchmarkSource, ReportSink, Clock) when a second adapter or a test substitute is needed. Today `utc_now` makes the report's times untestable from the CLI.

## 7. Checking the design against the code (as-built)

Generate the as-built sequence from a test that exercises this design, and compare it with section 3:

```bash
uv run python .claude/skills/vbench-docs/scripts/asbuilt.py sequence \
  "tests/test_cli.py::test_run_end_to_end" -o docs/usecases/UC-006-run-complete-evaluation/diagrams/as-built/sequence.puml
```

For the startup error, trace `tests/test_cli.py::test_missing_api_key_is_reported_before_running`, which uses the real `create_connector` with the key's variable unset.

A difference is either design drift (update this page and say why) or a code bug (fix the code). See [ADR-002](../../decisions/ADR-002.md).
