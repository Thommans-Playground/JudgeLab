# UC-005 Design: Generate report

> **Draft for review.** Design says *how* the code realises the [analysis](analysis.md): real classes, signatures, patterns and where they sit in the [hexagonal architecture](../../design.md). It describes the reference solution the codealongs build.

| Field | Value |
|---|---|
| Use case | [UC-005](README.md) |
| Slices | [T-005-01](T-005-01-aggregate-calculations.md) (aggregate calculations), [T-005-02](T-005-02-json-report-writer.md) (JSON report writer) |
| Code | `judgelab.scoring`, `judgelab.report`, called from `judgelab.cli.run_command` |
| Decisions | [ADR-001](../../decisions/ADR-001.md) (hexagonal), [ADR-002](../../decisions/ADR-002.md) (diagrams, as-built check) |

## 1. From analysis to design

| Analysis class | Design element | Hexagon role |
|---|---|---|
| Report Store (boundary) | `report.write_report(report, directory) -> Path` | Edge I/O, no port in v0.1 |
| Generate Report (control) | `scoring.summarise()`, then `report.build_report()`, then `report.write_report()`, called in that order by `cli.run_command()` | Application service, spread over three functions |
| Evaluation Run (entity) | `report.RunInfo` plus the `list[CaseResult]` from `runner.evaluate()` | Core (implicit aggregate) |
| Case Result (entity) | `scoring.CaseResult`, with `scoring.Outcome` | Core entity (Evaluation) |
| Connection Description (entity) | the dict from `report._connection(connector)`: `provider`, `model`, `base_url` | Core (Published Language) |
| Run Summary (entity) | `scoring.Summary`, with `evaluated`, `pass_rate`, `coverage` as properties | Core value object (Evaluation) |
| Report (entity) | the `dict` from `build_report()`, `REPORT_VERSION = "1"` | Core value (Published Language) |
| Case Entry (entity) | the dict from `report._case(result)`, with `_call(response)` for each model call | Core (part of the report) |

The **Evaluation Run** has no class in v0.1. It is implicit: `runner.evaluate()` returns a `list[CaseResult]`, and the run's identity and times live in `RunInfo` (see [Evaluation](../../domain/evaluation/README.md) and [Reporting](../../domain/reporting/README.md)). `build_report` takes both and puts them back together.

The **Report** is a plain `dict`, not a class. Its shape is the contract with the reader (JSON `report_version` "1"), and a dict serialises to exactly that shape with `json.dumps`. A class would only duplicate the schema.

## 2. Design classes

Diagram: [UC-005 design classes](diagrams/design-classes.puml)

## 3. Design sequences

**Main success scenario.** The CLI holds the results and the run's metadata, and asks for a summary, a report and a file:

Diagram: [UC-005 design sequence](diagrams/design-sequence.puml)

**Extension 1a.** No case reached a verdict. `pass_rate` is `None` (JSON `null`), `coverage` is `0.0`, and the CLI prints "Pass rate: n/a":

Diagram: [UC-005 design sequence, no verdicts](diagrams/design-sequence-no-verdicts.puml)

## 4. Patterns and principles

| Pattern / principle | Where | Why |
|---|---|---|
| Value objects | `CaseResult`, `Summary`, `RunInfo` are frozen dataclasses | A recorded result or summary can't change after the fact |
| Derived values as properties | `Summary.evaluated`, `pass_rate`, `coverage` | Only the four counts are stored, so the rates can never disagree with them |
| Single pass over an iterable | `summarise(results: Iterable[CaseResult])` | Works on a generator that can be read only once (AC-005-01) |
| Published Language | `build_report` returns the `report_version` "1" dict | Reviewers and tools read one stable, versioned shape (AC-005-05) |
| Conformist | `report` reads `CaseResult`, `Summary`, `ModelResponse` and connector identity as they are | Reporting doesn't translate the Evaluation model, it publishes it |
| Separate build from write | `build_report` is pure, `write_report` does the I/O | The report's content is tested without files (AC-005-04, AC-005-05); the file rules are tested on their own (AC-005-07) |
| Secrets by construction | `_connection` copies only `provider`, `model`, `base_url` | No code path can put a key or its variable name in the report (AC-005-06) |

## 5. Rules from the analysis, and where the design keeps them

| Rule | Kept by |
|---|---|
| Single pass | `summarise` loops once, counting into a dict keyed by `Outcome`, and counts `total` in the same loop |
| ERROR is never FAIL; null pass rate | `Summary.pass_rate` is `passed / evaluated`, or `None` when `evaluated` is 0; errors are only in `Summary.errors` |
| Coverage next to the pass rate | `Summary.coverage` is `evaluated / total`, or `0.0` when `total` is 0; `build_report` writes both into `summary`, with `errors` |
| Evidence per case; a missing stage is null | `_case` writes `None` for `actual_answer`, `refusal` and `target_call` when `result.target` is `None`, and for `verdict`, `justification` and `judge_call` when `result.judgement` is `None`; `error` is `{"stage", "message"}` only when `result.error` is set |
| What, with what, when | `build_report` writes `run` (id, `started_at`, `finished_at` via `isoformat()`, `judgelab_version` from package metadata), `benchmark`, `rubric`, `connections` |
| No key, no key variable name | `_connection` reads only `provider`, `model`, `base_url`; `ModelConnector` doesn't keep `api_key_env`, and the key lives inside the SDK client |
| Unique, time-stamped file; directory created | `write_report` calls `mkdir(parents=True, exist_ok=True)` and names the file `run-<started_at as %Y%m%dT%H%M%SZ>-<run_id[:8]>.json` |

## 6. Design notes and candidate refactorings

- **EvaluationRun aggregate.** The run is implicit: a `list[CaseResult]` plus `RunInfo`, joined only by the CLI. An `EvaluationRun` class holding the id, the times, the benchmark, the connections and the results would own the invariant "one CaseResult per TestCase", produce its own `Summary`, and be the single thing `build_report` takes. It is the main candidate refactoring of v0.1 (see [Evaluation](../../domain/evaluation/README.md)).
- **No application service for this use case.** Steps 1 to 6 are three calls inside `cli.run_command`. A `generate_report(run, results, directory) -> Path` function would give UC-005 one entry point that tests and other drivers could call.
- **`write_report` re-reads its own input.** It parses `started_at` back from the dict to build the file name. Passing `RunInfo` (or the aggregate) would avoid the round trip through a string.
- **`ReportSink` port.** `write_report` writes straight to the file system. By the rule in [ADR-001](../../decisions/ADR-001.md), a port comes when a second sink (for example, an upload) or a test double is needed. `utc_now` is the same case for a `Clock` port.
- **The time format in the name** ends in a literal `Z` from the format string, which is correct only because `started_at` is always UTC (`utc_now`). A naive or non-UTC datetime would get a wrong name. The aggregate could enforce UTC on construction.
- **Empty benchmark.** Extension 1a mentions an empty benchmark, and `summarise([])` handles it, but `load_benchmark` rejects a benchmark with no cases, so a real run never has `total == 0`.

## 7. Checking the design against the code (as-built)

Generate the as-built sequence from a test that exercises this design, and compare it with section 3:

```bash
uv run python .claude/skills/vbench-docs/scripts/asbuilt.py sequence \
  "tests/test_report.py::test_written_as_json_with_a_unique_name" -o docs/usecases/UC-005-generate-report/diagrams/as-built/sequence.puml
```

The test's fixture calls `summarise` and `build_report`, and the test calls `write_report`, so the trace covers the main success scenario. For extension 1a, trace `tests/test_scoring.py::test_pass_rate_is_none_when_nothing_was_evaluated`.

A difference is either design drift (update this page and say why) or a code bug (fix the code). See [ADR-002](../../decisions/ADR-002.md).
