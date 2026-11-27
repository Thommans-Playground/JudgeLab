# UC-004 Analysis: Evaluate responses

> **Draft for review.** Analysis describes *what* has to happen, in the problem's words: no Python, no SDKs, no patterns. The [design](design.md) says how the code does it.

| Field | Value |
|---|---|
| Use case | [UC-004](README.md) |
| Criteria | [UC-004.feature](UC-004.feature) |
| Bounded context | [Evaluation](../../domain/evaluation/README.md), using [Model Access](../../domain/model-access/README.md) and [Benchmark](../../domain/benchmark/README.md) |
| Ontology | [TestCase](../../ontology/test-case.md), [Rubric](../../ontology/rubric.md), [JudgeModel](../../ontology/judge-model.md), [Verdict](../../ontology/verdict.md), [JudgeEvaluation](../../ontology/judge-evaluation.md), [Outcome](../../ontology/outcome.md) |

## 1. System sequence diagram

The system is a black box. The diagram shows only what crosses its boundary: the judge request going out, and a verdict or an error coming back. It is the main success scenario and its extensions, drawn.

![UC-004 system sequence diagram](diagrams/ssd.svg)

Source: [diagrams/ssd.puml](diagrams/ssd.puml)

**System operations** found here:

| Operation | Responsibility | Postcondition |
|---|---|---|
| judge request (out) | Ask the judge model for a verdict on one answer, under a rubric | The judge has received the case as data and the rubric as instructions |
| record evaluation | Keep a validated verdict with its justification, rubric and judge identity | A Judge Evaluation exists for the case (AC-004-04) |
| record ERROR | Keep the reason no verdict exists | The case is ERROR, never FAIL (AC-004-03) |

## 2. Analysis classes

Found by reading the use case's nouns and splitting them by role:

- **Boundary:** where the system meets something outside it. Here, the judge model.
- **Control:** the use case's logic, the steps of the main flow. One per use case is typical.
- **Entity:** information the problem cares about, which outlives one step.

![UC-004 analysis classes](diagrams/analysis-classes.svg)

Source: [diagrams/analysis-classes.puml](diagrams/analysis-classes.puml)

| Analysis class | Role | Comes from (use case text) | Ontology concept |
|---|---|---|---|
| Judge Model Interface | Boundary | "sends the prompt to the judge model" | JudgeModel |
| Evaluate Response | Control | the main success scenario, steps 1 to 5 | — |
| Test Case | Entity | "the question, the expected answer" | TestCase |
| Actual Answer | Entity | "the target's answer, or its refusal" | ModelResponse, Refusal |
| Rubric | Entity | "the rubric … chosen by id" | Rubric |
| Judge Request | Entity | "builds the judge's prompt … as instructions" | — (exists only during the call) |
| Judge Evaluation | Entity | "records the evaluation" | JudgeEvaluation |
| Verdict | Entity | "the verdict is PASS or FAIL" | Verdict |

## 3. Analysis sequence

How the analysis objects work together to deliver the main success scenario. The control object drives the work, entities hold the information, and only the boundary talks to the outside.

![UC-004 analysis sequence](diagrams/analysis-sequence.svg)

Source: [diagrams/analysis-sequence.puml](diagrams/analysis-sequence.puml)

## 4. Rules the design must keep

These come from the use case's business rules and its scenarios. The design is checked against them.

1. A judgement that cannot be trusted produces no Judge Evaluation, and the case becomes ERROR, never FAIL (AC-004-03).
2. The answer being judged is data: it travels inside its own tag, and the rubric says so (AC-004-01).
3. The judge's identity is recorded with every evaluation: both the requested and the served model (AC-004-04).
4. Changing the judge is a configuration change. Nothing in Evaluate Response depends on which provider answers (AC-004-05).
