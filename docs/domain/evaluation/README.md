# Evaluation

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Code | `judgelab.runner`, `judgelab.judge`, `judgelab.scoring` |
| Responsibility | Deciding each test case's Outcome (PASS, FAIL or ERROR) and summarising a run honestly |

## Purpose

This context is the heart of JudgeLab. It runs a benchmark against a target model, asks a judge model whether each answer is correct under a rubric, and decides each case's final Outcome. Then it counts the outcomes into a summary.

Its central rule is honesty about what we know. PASS and FAIL need a verdict we can trust. Anything that stops a trustworthy verdict, such as a failed call, a cut-off answer or a judge reply we cannot parse, is ERROR, never FAIL. And ERROR cases never drag down the pass rate.

It deliberately does **not** own:

- how to reach a model, read a key or talk to an SDK (Model Access);
- what a valid benchmark file looks like (Benchmark);
- how a run is written down for reviewers (Reporting);
- reading the YAML config or printing progress (the application layer).

## Ubiquitous language

Every model and event file in this folder must have a row here (the docs check enforces this).

| Term | DDD Type | Ontology | Meaning in this context |
|---|---|---|---|
| [EvaluationRun](evaluation-run.md) | Aggregate Root | `EvaluationRun` | One execution of a benchmark against a target, with a judge and a rubric. Implicit in v0.1. |
| [CaseResult](case-result.md) | Entity | `CaseResult` | Everything that happened to one test case in a run, ending in one Outcome. |
| [TargetResult](target-result.md) | Value Object | `ModelResponse` | The target's answer to one case: a ModelResponse, or the ConnectorError that stopped it. |
| [Rubric](rubric.md) | Value Object | `Rubric` | Named instructions telling the judge what counts as a correct answer. |
| [Verdict](verdict.md) | Value Object | `Verdict` | The judge's decision on one answer: PASS or FAIL. |
| [JudgeEvaluation](judge-evaluation.md) | Value Object | `JudgeEvaluation` | A validated verdict with its justification, the rubric id and the judge's ModelResponse. |
| [Outcome](outcome.md) | Value Object | `Outcome` | A case's final state: PASS, FAIL or ERROR. |
| [RunSummary](run-summary.md) | Value Object | `RunSummary` | Counts of outcomes, plus pass rate and coverage. |
| [Judge](judge.md) | Domain Service | `JudgeModel` | Asks the judge model for a verdict on one answer, and accepts only a well-formed one. |
| [Scorer](scorer.md) | Domain Service | `RunSummary` | Counts a run's outcomes in a single pass. |
| [CaseExecuted](case-executed.md) | Domain Event | `ModelResponse` | A case was sent to the target (answered, refused, failed or not sent). |
| [CaseEvaluated](case-evaluated.md) | Domain Event | `CaseResult` | A case reached its final Outcome. |

Two roles matter here and are easy to mix up. The **target** (ontology `TargetModel`) is the model being tested. The **judge** (ontology `JudgeModel`) is the model doing the grading. Both are reached through a Model Access `ModelConnector`; only this context knows which is which.

## Relationships with other contexts

| Context | Relationship | Integration (what crosses the boundary) |
|---|---|---|
| [Model Access](../model-access/README.md) | Customer (downstream) of an Open Host Service with a Published Language | Calls `ModelConnector.generate(prompt, instructions=...)`. Receives `ModelResponse`, or catches `ConnectorError` and its subclasses. |
| [Benchmark](../benchmark/README.md) | Conformist (downstream) | Uses `Benchmark` and `TestCase` as they are, with no translation. |
| [Reporting](../reporting/README.md) | Upstream; Reporting is Conformist | Reporting reads `CaseResult`, `RunSummary`, `JudgeEvaluation` and `Outcome` directly. |
| Application layer (`cli`) | Not a context: driving adapter and composition root | `cli.run_command` builds the `Judge`, calls `runner.evaluate`, subscribes to CaseEvaluated for the progress line, and calls `summarise`. |

## Domain events

| Event | Published / Consumed | Counterpart context |
|---|---|---|
| [CaseExecuted](case-executed.md) | Published by `runner.run_target` / `runner.evaluate` | None in v0.1 (tests subscribe) |
| [CaseEvaluated](case-evaluated.md) | Published by `runner.evaluate` | Application layer (CLI progress line) |

## Policies and cross-aggregate rules

- **Every test case ends with exactly one CaseResult**, in benchmark order, even when the run is stopped (AC-003-01, AC-006-01).
- **A connector error on one case is recorded and the run continues** (AC-003-02).
- **Auth and quota errors stop the run.** They will repeat on every call (`runner.STOP_THE_RUN`). After one on the target, the remaining cases are not sent and get the error `not sent: run stopped after <Error> on case <id>` (AC-003-03). After one on the judge, the remaining cases are not judged and get `not judged: judging stopped after <Error> on case <id>` at the judge stage (AC-006-03).
- **An untrusted target answer is ERROR and is never judged.** That covers a connector error and a **truncated answer**: `answer was cut off by its length limit`, at the target stage (AC-006-02).
- **A refusal is still judged.** The judge receives `[refused] <explanation>` as the actual answer and decides whether refusing was right (AC-006-04).
- **A judge failure is ERROR at the judge stage, never FAIL.** That covers a failed judge call, a judge refusal, a truncated judge reply, invalid JSON, an unsupported verdict or a missing justification (AC-004-03, AC-006-03).
- **Only a verdict makes PASS or FAIL.** `Outcome(judgement.verdict)` is the only way to reach them.
- **Pass rate excludes ERROR cases**: passed / (passed + failed) (AC-005-02).
- **Bugs are not hidden.** Only `ConnectorError` is caught. Any other exception ends the run (AC-003-05).
- **Target first, then judge.** `evaluate` sends every case to the target before judging any of them.
