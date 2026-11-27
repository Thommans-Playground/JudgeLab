# UC-005: Generate report

| Field | Value |
|---|---|
| Primary actor | Developer |
| Requirements | REQ-009, REQ-010, REQ-013 |
| Introduced in | v0.1 |
| Status | Draft |

## Goal

Every run ends with a JSON report that a reviewer can trust without rerunning anything. It holds the evidence for each case, what was run and with which models, and a summary that keeps errors visible. An error must never be hidden inside the pass rate, and a key must never end up in the file.

> **Draft for review.** The flow and the scenarios were drafted from the [v0.1 release plan](../../releases/v0.1/README.md), whose release acceptance rules for totals, pass rate and coverage they keep.

**Trigger:** every case of a run has an outcome: PASS, FAIL or ERROR (UC-006).

## Preconditions

- One result per case, each with its outcome and whatever evidence exists: the target's answer or refusal, the judge's evaluation, or an error with its stage (UC-003, UC-004).
- The run's metadata: the benchmark, the rubric id, both connections, and the UTC start and finish times.
- An output directory, from the config or from `--output-dir` (UC-006).

## Main success scenario

1. The system counts the outcomes in one pass over the results: total, passed, failed and errors.
2. The system works out `evaluated` (passed + failed), `pass_rate` (passed / evaluated) and `coverage` (evaluated / total).
3. The system builds the report: `report_version`, `run` (id, `started_at`, `finished_at`, `judgelab_version`), `benchmark` (id, name, number of cases), `rubric`, `connections` (target and judge, each with provider, model and base URL), `summary`, and one entry per case.
4. Each case entry records its id, question, expected answer, actual answer, refusal, outcome, verdict and justification, the target call and the judge call (requested and served model, finish reason, tokens, request id, latency), and its error, if any.
5. The system creates the output directory if needed and writes the report there as UTF-8 JSON, named `run-<UTC start time>-<first 8 characters of the run id>.json`.
6. The system returns the path of the report, which the CLI prints (UC-006).

## Extensions / alternate flows

- **1a.** No case reached a verdict, because every case is ERROR or the benchmark is empty: `pass_rate` is `null`, not 0, and `coverage` is 0.0. The CLI prints "Pass rate: n/a (no case reached a verdict)".
- **4a.** The case failed at the target: `actual_answer`, `verdict`, `justification`, `target_call` and `judge_call` are `null`, and `error` holds `{"stage": "target", "message": ...}`.
- **4b.** The target answered but the judge failed: the target's evidence is kept, `verdict`, `justification` and `judge_call` are `null`, and `error` has the stage `judge`.
- **4c.** The target refused: `actual_answer` is `null` and `refusal` holds the refusal text, next to the judge's verdict on it (UC-006).
- **5a.** The output directory, or one of its parents, does not exist: it is created.

## Postconditions

- A JSON report exists in the output directory, with a name no other run will use, and holds the full evidence and the summary of the run.
- The report contains no API key and no name of a key's environment variable.

## Business rules

- An ERROR is never counted as a FAIL. It lowers coverage, not the pass rate.
- The pass rate is always shown next to the error count and the coverage, so a high rate with low coverage can't pass unnoticed.
- A connection is described by its provider, model and base URL only. Its `api_key_env`, and the key itself, never reach the report.
- Times are UTC, in ISO 8601.

## Acceptance criteria

Defined as Gherkin scenarios in [UC-005.feature](UC-005.feature): one Scenario per criterion, tagged with its ID. Tests are marked with the same IDs, so pytest's progress table shows which ones pass.

## Slices

Each slice is a task file in this folder that makes some of the criteria pass.

| Task | Slice | Delivers | Status |
|---|---|---|---|
| [T-005-01](T-005-01-aggregate-calculations.md) | Aggregate calculations | AC-005-01, AC-005-02, AC-005-03 | Todo |
| [T-005-02](T-005-02-json-report-writer.md) | JSON report writer | AC-005-04, AC-005-05, AC-005-06, AC-005-07 | Todo |
