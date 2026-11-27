# UC-006 Analysis: Run complete evaluation

> **Draft for review.** Analysis describes *what* has to happen, in the problem's words: no Python, no SDKs, no patterns. The [design](design.md) says how the code does it.

| Field | Value |
|---|---|
| Use case | [UC-006](README.md) |
| Criteria | [UC-006.feature](UC-006.feature) |
| Bounded context | Spans all four: [Model Access](../../domain/model-access/README.md), [Benchmark](../../domain/benchmark/README.md), [Evaluation](../../domain/evaluation/README.md) and [Reporting](../../domain/reporting/README.md), coordinated by the application layer (the command line and the config file) |
| Ontology | [EvaluationRun](../../ontology/evaluation-run.md), [Benchmark](../../ontology/benchmark.md), [Rubric](../../ontology/rubric.md), [ConnectionProfile](../../ontology/connection-profile.md), [CaseResult](../../ontology/case-result.md), [Outcome](../../ontology/outcome.md), [RunSummary](../../ontology/run-summary.md), [Report](../../ontology/report.md) |

## 1. System sequence diagram

The system is a black box. The diagram shows only what crosses its boundary: the developer's command and what is printed back, the calls to the target and the judge, and the report going out. It is the main success scenario and its extensions, drawn. UC-001 to UC-005 are the steps inside; this use case is the one the developer starts.

Diagram: [UC-006 system sequence diagram](diagrams/ssd.puml)

**System operations** found here:

| Operation | Responsibility | Postcondition |
|---|---|---|
| run(config file, output directory?) | Check the whole setup, then evaluate every case and report the run | Every case has exactly one outcome and a report exists; or nothing was called and nothing was written (AC-006-05, AC-006-06) |
| error (out) | Explain in one line why the run cannot start | Exit code 1, no model called, no report written, no traceback, no pasted key echoed (AC-006-06) |
| question (out) | Ask the target one case's question | The target answered, refused or failed (UC-003, AC-006-02) |
| judge request (out) | Ask the judge for a verdict on an answer that can be trusted | A verdict, or an ERROR at the judge stage (UC-004, AC-006-01, AC-006-03, AC-006-04) |
| progress line (out) | Show each case's outcome as it is decided | The developer sees `[i/n] id: OUTCOME`, with the stage and message for an ERROR (AC-006-05) |
| write report (out) | Publish the run as evidence | A report exists in the chosen output directory (UC-005, AC-006-07) |
| totals (out) | Show passed, failed, errors, pass rate with coverage, and the report's path | Exit code 0, whatever the verdicts (AC-006-05, extension 7a) |

## 2. Analysis classes

Found by reading the use case's nouns and splitting them by role:

- **Boundary:** where the system meets something outside it. Here, the developer's command line, the config file, the two models and the output directory.
- **Control:** the use case's logic, the steps of the main flow. One per use case is typical.
- **Entity:** information the problem cares about, which outlives one step.

Diagram: [UC-006 analysis classes](diagrams/analysis-classes.puml)

| Analysis class | Role | Comes from (use case text) | Ontology concept |
|---|---|---|---|
| Command Line | Boundary | "runs `judgelab run --config <file>`", "prints … exits with code 0" | — |
| Config File | Boundary | "a YAML config file naming the target and judge connections, the dataset, the rubric id and … the output directory" | — |
| Model Interface | Boundary | "sends the question to the target", "sends the target's answer to the judge" | TargetModel, JudgeModel, ModelConnector |
| Report Store | Boundary | "writes the report to the output directory" | — |
| Run Evaluation | Control | the main success scenario, steps 1 to 7 | — |
| Evaluation Config | Entity | "the dataset, the rubric id and, optionally, the output directory (default `reports`)" | — (application layer) |
| Connection Profile | Entity | "the target and judge connections", "each connection's `api_key_env`" | ConnectionProfile |
| Benchmark | Entity | "the benchmark's name and number of cases" | Benchmark, TestCase |
| Rubric | Entity | "the judge with its rubric" | Rubric |
| Evaluation Run | Entity | "every case answered by the target, judged by the judge, and written to a report" | EvaluationRun |
| Case Result | Entity | "the judge's verdict becomes the case's outcome", "every ERROR names its stage" | CaseResult, Outcome |
| Run Summary | Entity | "the totals, the pass rate with the coverage" | RunSummary |

The **Evaluation Run** is the aggregate this use case creates. In v0.1 it is implicit: no single object holds it, only the list of Case Results plus the run's metadata (its id, the benchmark, rubric, connections and start and finish times). The design keeps it that way and lists a real aggregate as a candidate refactoring.

A **case evaluated** event happens each time a case reaches its final outcome. The progress line is its only consumer in v0.1.

## 3. Analysis sequence

How the analysis objects work together to deliver the main success scenario. The control object drives the work, entities hold the information, and only the boundaries talk to the outside.

Diagram: [UC-006 analysis sequence](diagrams/analysis-sequence.puml)

## 4. Rules the design must keep

These come from the use case's business rules and its scenarios. The design is checked against them.

1. Setup problems (config, connections, keys, dataset, rubric) are all found before the first model call. They end the run with one `error:` line on stderr and exit code 1, with no traceback, no report and no pasted key echoed (AC-006-06, extension 1a).
2. A missing `--config` is a usage error with exit code 2 (extension 1c).
3. The config names everything a run needs, and `--output-dir` overrides its output directory, which defaults to `reports` (AC-006-07, extension 1b).
4. The judge's verdict is the case's outcome (AC-006-01).
5. An answer that can't be trusted (a target failure or a cut-off answer) is ERROR at the `target` stage and is never judged (AC-006-02, extension 3a).
6. A judge failure is ERROR at the `judge` stage, never FAIL. After a judge auth or quota failure, the remaining cases are not judged (AC-006-03, extension 4a).
7. A refusal is judged as the answer, marked `[refused]` (AC-006-04, extension 3b).
8. Each case's outcome is shown as it is decided, then the totals, the pass rate with the coverage, and the report path (AC-006-05, extension 7a).
9. Exit code 0 means the run completed, whatever the verdicts. Exit code 1 means it could not start.
10. Swapping the target and the judge is a configuration change only (AC-006-11). Live runs happen only when asked for (AC-006-08 to AC-006-10).
