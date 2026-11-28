# UC-006: Run complete evaluation

| Field | Value |
|---|---|
| Primary actor | Developer |
| Requirements | REQ-003, REQ-005, REQ-006, REQ-008, REQ-011, REQ-013 |
| Introduced in | v0.1 |
| Status | Draft |

## Goal

A developer runs one command and gets an evaluated benchmark: every case answered by the target, judged by the judge, and written to a report. A broken setup is caught before any model is called, and a failure during the run becomes an explicit ERROR on the case it hit, never a FAIL.

> **Draft for review.** The flow and the scenarios were drafted from the [v0.1 release plan](../../releases/v0.1/README.md), whose release acceptance and validation gate (one live run, reviewed by hand) they keep.

**Trigger:** the developer runs `judgelab run --config <file>`, optionally with `--output-dir <dir>`.

## Preconditions

- A YAML config file naming the target and judge connections, the dataset, the rubric id and, optionally, the output directory (default `reports`).
- The environment variables named by each connection's `api_key_env`, such as `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`, are set.
- The dataset file exists and is a valid benchmark (UC-002).

## Main success scenario

1. The system loads the config, the benchmark and the rubric, and creates the target and judge connectors (UC-001).
2. The system prints the benchmark's name and number of cases, the target, and the judge with its rubric.
3. For each case, in order, the system sends the question to the target (UC-003).
4. The system sends the target's answer to the judge with the question and the expected answer (UC-004).
5. The judge's verdict becomes the case's outcome, PASS or FAIL, and the system prints a progress line such as `[1/5] gk-001: PASS`.
6. When every case has an outcome, the system writes the report to the output directory (UC-005).
7. The system prints the totals, the pass rate with the coverage, and the report's path, then exits with code 0.

## Extensions / alternate flows

- **1a.** The config file is missing, is not valid YAML, has an unknown section or setting, holds a pasted key instead of a variable name, names an unknown rubric or a missing dataset, or a key's variable is not set: the system prints a one-line `error:` message to stderr and exits with code 1. No model is called, no traceback is shown, no report is written, and a pasted key is never echoed.
- **1b.** `--output-dir` is given: the report goes there instead of the config's output directory.
- **1c.** `--config` is missing: the argument parser prints its usage and exits with code 2.
- **3a.** The target fails, or its answer is cut off by the length limit: the case is ERROR at the `target` stage and is not sent to the judge. An auth or quota failure stops the remaining target calls, and those cases are ERROR too (UC-003).
- **3b.** The target refuses: the refusal is sent to the judge as the answer, marked `[refused]`, so the judge decides whether refusing was right.
- **4a.** The judge fails or its reply can't be trusted: the case is ERROR at the `judge` stage, never FAIL. After a judge auth or quota failure, the remaining cases are not judged and are ERROR at the `judge` stage.
- **7a.** No case reached a verdict: the summary prints "Pass rate: n/a (no case reached a verdict)". The run still completes, writes its report and exits with code 0.

## Postconditions

- Every case has exactly one outcome, PASS, FAIL or ERROR, and every ERROR names its stage.
- A report exists for the run (UC-005), or, when the setup was invalid, nothing was called and nothing was written.

## Business rules

- Setup problems are found before the first model call, so a bad config costs nothing.
- An ERROR is never turned into a FAIL, and an answer we can't trust is never judged.
- Exit code 0 means the run completed, whatever the verdicts. Exit code 1 means it could not start.
- Live checks against real models cost money. They run only when asked for, with real keys.

## Acceptance criteria

Defined as Gherkin scenarios in [UC-006.feature](UC-006.feature): one Scenario per criterion, tagged with its ID. Tests are marked with the same IDs, so pytest's progress table shows which ones pass. AC-006-08 runs only with `pytest -m live`, and AC-006-09 to 11 are checked by hand, with the release report as evidence.

## Analysis and design

- [Analysis](analysis.md): analysis class and sequence diagrams (boundary, control, entity), in problem terms.
- [Design](design.md): design class and sequence diagrams in code terms, the patterns used, and how to check the code against them (as-built).

## Slices

Each slice is a task file in this folder that makes some of the criteria pass.

| Task | Slice | Delivers | Status |
|---|---|---|---|
| [T-006-01](T-006-01-cli-and-orchestration.md) | CLI and orchestration | AC-006-01, AC-006-02, AC-006-03, AC-006-04, AC-006-05, AC-006-06, AC-006-07 | Todo |
| [T-006-02](T-006-02-live-end-to-end-benchmark.md) | Live end-to-end benchmark | AC-006-08, AC-006-09, AC-006-10, AC-006-11 | Todo |
