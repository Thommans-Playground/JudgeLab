# UC-005 Analysis: Generate report

> **Draft for review.** Analysis describes *what* has to happen, in the problem's words: no Python, no SDKs, no patterns. The [design](design.md) says how the code does it.

| Field | Value |
|---|---|
| Use case | [UC-005](README.md) |
| Criteria | [UC-005.feature](UC-005.feature) |
| Bounded context | [Reporting](../../domain/reporting/README.md), conforming to [Evaluation](../../domain/evaluation/README.md) |
| Ontology | [EvaluationRun](../../ontology/evaluation-run.md), [CaseResult](../../ontology/case-result.md), [Outcome](../../ontology/outcome.md), [RunSummary](../../ontology/run-summary.md), [Report](../../ontology/report.md), [ConnectionProfile](../../ontology/connection-profile.md) |

## 1. System sequence diagram

The system is a black box. The diagram shows only what crosses its boundary: the report file going out to the output directory, and its path coming back to the developer. Everything else, counting and building, happens inside. It is the main success scenario and its extensions, drawn.

![UC-005 system sequence diagram](diagrams/ssd.svg)

Source: [diagrams/ssd.puml](diagrams/ssd.puml)

**System operations** found here:

| Operation | Responsibility | Postcondition |
|---|---|---|
| summarise run | Count the outcomes in one pass and work out evaluated, pass rate and coverage | A Run Summary exists; ERROR cases are counted as errors, never as failures (AC-005-01, AC-005-02, AC-005-03) |
| build report | Put the run's metadata, its summary and every case's evidence into one document | A Report holds what was run, with what, when, and the evidence per case (AC-005-04, AC-005-05) |
| write report (out) | Store the report as UTF-8 JSON in the output directory, under a name no other run uses | The file exists, the directory was created if needed, and the file holds no key and no key variable name (AC-005-06, AC-005-07) |
| report path (out) | Tell the developer where the report is | The developer can open the report (UC-006 prints the path) |

## 2. Analysis classes

Found by reading the use case's nouns and splitting them by role:

- **Boundary:** where the system meets something outside it. Here, the output directory the report is written to.
- **Control:** the use case's logic, the steps of the main flow. One per use case is typical.
- **Entity:** information the problem cares about, which outlives one step.

![UC-005 analysis classes](diagrams/analysis-classes.svg)

Source: [diagrams/analysis-classes.puml](diagrams/analysis-classes.puml)

| Analysis class | Role | Comes from (use case text) | Ontology concept |
|---|---|---|---|
| Report Store | Boundary | "writes the report there as UTF-8 JSON" | — (the output directory) |
| Generate Report | Control | the main success scenario, steps 1 to 6 | — |
| Evaluation Run | Entity | "the run's metadata: the benchmark, the rubric id, both connections, and the UTC start and finish times" | EvaluationRun |
| Case Result | Entity | "one result per case, each with its outcome and whatever evidence exists" | CaseResult, Outcome |
| Connection Description | Entity | "each with provider, model and base URL" | ConnectionProfile (its public part only) |
| Run Summary | Entity | "total, passed, failed and errors … `evaluated` … `pass_rate` … `coverage`" | RunSummary |
| Report | Entity | "`report_version`, `run`, `benchmark`, `rubric`, `connections`, `summary`, and one entry per case" | Report |
| Case Entry | Entity | "each case entry records its id, question, expected answer …" | — (part of Report) |

The **Evaluation Run** is the aggregate the report publishes. In v0.1 it is implicit: no single object holds it, only the list of Case Results plus the run's metadata (identity, benchmark, rubric, connections and times). The design keeps it that way and lists a real aggregate as a candidate refactoring.

## 3. Analysis sequence

How the analysis objects work together to deliver the main success scenario. The control object drives the work, entities hold the information, and only the boundary talks to the outside.

![UC-005 analysis sequence](diagrams/analysis-sequence.svg)

Source: [diagrams/analysis-sequence.puml](diagrams/analysis-sequence.puml)

## 4. Rules the design must keep

These come from the use case's business rules and its scenarios. The design is checked against them.

1. Outcomes are counted in a single pass, so results that can be read only once are still counted correctly (AC-005-01).
2. An ERROR is never a FAIL. The pass rate is passed / (passed + failed), and it is null, not 0, when no case reached a verdict (AC-005-02, extension 1a).
3. Coverage is evaluated / total, and 0.0 when there are no cases. It is always reported next to the pass rate and the error count (AC-005-03).
4. Every case carries its evidence, and a stage that did not happen is null, never invented: no target call after a target failure, no judge call after a judge failure (AC-005-04, extensions 4a to 4c).
5. The report records what was run, with what, and when, with UTC times in ISO 8601 (AC-005-05).
6. A connection is described by provider, model and base URL only. No key, and no key variable name, reaches the report (AC-005-06).
7. The file name is unique per run and time-stamped, and a missing output directory is created (AC-005-07, extension 5a).
