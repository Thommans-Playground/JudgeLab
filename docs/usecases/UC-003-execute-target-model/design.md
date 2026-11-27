# UC-003 Design: Execute target model

> **Draft for review.** Design says *how* the code realises the [analysis](analysis.md): real classes, signatures, patterns and where they sit in the [hexagonal architecture](../../design.md). It describes the reference solution the codealongs build.

| Field | Value |
|---|---|
| Use case | [UC-003](README.md) |
| Slices | [T-003-01](T-003-01-target-inference.md) (target inference) |
| Code | `judgelab.runner.run_target`, called from `judgelab.runner.evaluate` |
| Decisions | [ADR-001](../../decisions/ADR-001.md) (hexagonal), [ADR-002](../../decisions/ADR-002.md) (diagrams, as-built check) |

## 1. From analysis to design

| Analysis class | Design element | Hexagon role |
|---|---|---|
| Target Model Interface (boundary) | `ModelConnector` port; adapters `OpenAIConnector`, `AnthropicConnector`, `FakeConnector` | Driven port + adapters |
| Progress Listener (boundary) | the `on_result` callback of `run_target`, which `evaluate` fills with its `on_target` | Observer (in-process event) |
| Execute Target (control) | `runner.run_target(benchmark, target, *, on_result=None)` | Application service |
| Benchmark (entity) | `benchmark.Benchmark` | Core (Benchmark context) |
| Test Case (entity) | `benchmark.TestCase` | Core (Benchmark context) |
| Target Result (entity) | `runner.TargetResult(case, response, error)` | Core value object |
| Model Response (entity) | `connectors.ModelResponse` | Port type |
| Connector Error (entity) | `connectors.ConnectorError` and its six subclasses | Port type |

The stop reason has no class. It is a local `stopped_by: tuple[str, ConnectorError] | None` in `run_target`, which lives for one call. Which errors stop the run is data: the tuple `STOP_THE_RUN = (ConnectorAuthError, ConnectorQuotaError)`, shared with `evaluate`'s stop-judging rule.

## 2. Design classes

Diagram: [UC-003 design classes](diagrams/design-classes.puml)

## 3. Design sequences

**Main success scenario.** Each case answered, each result emitted as a CaseExecuted event through the `on_target` callback:

Diagram: [UC-003 design sequence](diagrams/design-sequence.puml)

**Extensions 2a, 2b and 2c.** A connector error is recorded and the run goes on; an auth or quota error (`STOP_THE_RUN`) also stops it, so later cases are recorded as "not sent" without a call; any other exception escapes:

Diagram: [UC-003 design sequence, call failures and stopping](diagrams/design-sequence-stop.puml)

## 4. Patterns and principles

| Pattern / principle | Where | Why |
|---|---|---|
| Ports and adapters | `run_target` depends on the `ModelConnector` port, never on an SDK | The target can be any provider; tests use `FakeConnector` (AC-003-01 to AC-003-05) |
| Strategy | `ModelConnector` implementations are interchangeable | Switching target is configuration, not code |
| Observer (lightweight) | `on_result` / `on_target` callbacks, called synchronously with each `TargetResult` | Progress without `run_target` knowing who listens; this is the CaseExecuted event (AC-003-04) |
| Value objects | `TargetResult`, `ModelResponse` are frozen | A captured result can't change before it's judged |
| Errors as data | a `ConnectorError` is stored in `TargetResult.error`, not re-raised | One failed case doesn't cost the others (AC-003-02) |
| Policy as data | `STOP_THE_RUN` tuple and `isinstance(error, STOP_THE_RUN)` | The stopping rule is one line to read and one tuple to change (AC-003-03) |
| Catch narrowly | `except ConnectorError` only | Bugs stay visible (AC-003-05) |
| Test double (Fake) | `FakeConnector(replies=..., default=...)` records `prompts` | Tests prove "sent once, in order" and "never sent" by reading `target.prompts` |

## 5. Rules from the analysis, and where the design keeps them

| Rule | Kept by |
|---|---|
| One result per case, in order, response xor error | the single `for case in benchmark.cases` loop appends exactly one `TargetResult` per case; each branch sets one of `response` and `error` |
| One call per case | `target.generate(case.question)` is called at most once per loop pass; no retry loop in `run_target` |
| A connector error is data | `except ConnectorError as error: result = TargetResult(case, None, error)` |
| Auth or quota stops the run | `stopped_by = (case.id, error)` when `isinstance(error, STOP_THE_RUN)`; later passes build `ConnectorError(f"not sent: run stopped after {type(error).__name__} on case {failed_case}")` and skip `generate` |
| The listener hears every case | `on_result(result)` is called after every append, including failed and not-sent cases |
| Only connector errors are caught | no other `except` clause; `ZeroDivisionError` propagates |
| Refusal and cut-off are responses | `run_target` doesn't look inside `ModelResponse`; `runner._judge` makes a truncated answer ERROR and sends a refusal to the judge as `"[refused] ..."` |
| Any target works | `run_target` sees only `ModelConnector` |

## 6. Design notes and candidate refactorings

- **The callback has two names.** The spec's CaseExecuted event is `on_target` in `evaluate`, but `run_target`'s own parameter is called `on_result`, and `evaluate` also has an `on_result` for CaseEvaluated. So `on_result` means CaseExecuted in one function and CaseEvaluated in the other. Renaming `run_target`'s parameter to `on_target` would make the event name one name everywhere.
- **Nobody subscribes in v0.1.** `cli.run_command` passes only `on_result` (CaseEvaluated) to `evaluate`. CaseExecuted is used only by tests (`tests/test_evaluate.py::test_progress_callbacks_see_both_stages`).
- **The order of events is not interleaved.** `evaluate` calls `run_target` to the end before it judges anything, so every CaseExecuted fires before the first CaseEvaluated. A run that judged each case as soon as it was answered (a generator, or one loop) would show progress per case instead of per stage.
- **"Not sent" uses the base class.** A not-sent case's error is a plain `ConnectorError`, with no `status_code` or `request_id`. Reports can tell it apart only by its message. A `CaseNotSent` subclass, or a field on `TargetResult`, would make it a type, not a string.
- **Bug path and progress.** When a bug escapes (2c), `run_target` returns no results, but the callback has already heard about the cases before it. A listener that writes partial output should expect that.
- **An `EvaluationRun` aggregate** would own the run's stop state (`stopped_by` here, `judge_stopped_by` in `evaluate`) and its results, instead of local variables in two functions (see [Evaluation](../../domain/evaluation/README.md)).
- **Concurrency.** Cases run one at a time. Sending cases in parallel is a natural next step, but it would make "stop the run" a race and "in order" a sorting job, so it should come with the aggregate, not before.

## 7. Checking the design against the code (as-built)

Generate the as-built sequence from a test that exercises this design, and compare it with section 3:

```bash
uv run python .claude/skills/vbench-docs/scripts/asbuilt.py sequence \
  "tests/test_runner.py::test_each_question_is_sent_once_in_order" -o docs/usecases/UC-003-execute-target-model/diagrams/as-built/sequence.puml
```

For the stop extension, trace `tests/test_runner.py::test_auth_and_quota_errors_stop_the_run`.

A difference is either design drift (update this page and say why) or a code bug (fix the code). See [ADR-002](../../decisions/ADR-002.md).
