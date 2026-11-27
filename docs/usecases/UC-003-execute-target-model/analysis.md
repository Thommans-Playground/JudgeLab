# UC-003 Analysis: Execute target model

> **Draft for review.** Analysis describes *what* has to happen, in the problem's words: no Python, no SDKs, no patterns. The [design](design.md) says how the code does it.

| Field | Value |
|---|---|
| Use case | [UC-003](README.md) |
| Criteria | [UC-003.feature](UC-003.feature) |
| Bounded context | [Evaluation](../../domain/evaluation/README.md), using [Model Access](../../domain/model-access/README.md) and [Benchmark](../../domain/benchmark/README.md) |
| Ontology | [Benchmark](../../ontology/benchmark.md), [TestCase](../../ontology/test-case.md), [TargetModel](../../ontology/target-model.md), [ModelResponse](../../ontology/model-response.md), [Refusal](../../ontology/refusal.md), [ConnectorError](../../ontology/connector-error.md) |

## 1. System sequence diagram

The system is a black box. The diagram shows only what crosses its boundary: each question going out to the target, an answer or an error coming back, and progress going to the developer. It is the main success scenario and its extensions, drawn.

Diagram: [UC-003 system sequence diagram](diagrams/ssd.puml)

**System operations** found here:

| Operation | Responsibility | Postcondition |
|---|---|---|
| question (out) | Ask the target model one benchmark question, once | The target has received the question exactly once (AC-003-01) |
| record result | Keep what came back against its case: a model response or a connector error | The case has exactly one Target Result (AC-003-01, AC-003-02) |
| stop the run | After an auth or quota error, send nothing more | Every later case has a result with no response and the error "not sent: run stopped after … on case …" (AC-003-03) |
| case executed (progress) | Tell whoever is listening that a case has its result | The listener has heard about every case, in order (AC-003-04) |

A bug in the target code (extension 2c) is not a system operation. It leaves the system unchanged and reaches the caller as it is (AC-003-05).

## 2. Analysis classes

Found by reading the use case's nouns and splitting them by role:

- **Boundary:** where the system meets something outside it. Here, the target model, and the listener that hears about progress.
- **Control:** the use case's logic, the steps of the main flow. One per use case is typical.
- **Entity:** information the problem cares about, which outlives one step.

Diagram: [UC-003 analysis classes](diagrams/analysis-classes.puml)

| Analysis class | Role | Comes from (use case text) | Ontology concept |
|---|---|---|---|
| Target Model Interface | Boundary | "sends the case's question to the target" | TargetModel |
| Progress Listener | Boundary | "calls the progress callback … with that result" | — (the CaseExecuted event's subscriber) |
| Execute Target | Control | the main success scenario, steps 1 to 5 | — |
| Benchmark | Entity | "a loaded benchmark with at least one test case" | Benchmark |
| Test Case | Entity | "the next test case, in benchmark order" | TestCase |
| Target Result | Entity | "a result for the case: the case and the model response" | ModelResponse (as captured for a case) |
| Model Response | Entity | "the target replies"; "refuses, or its answer is cut off" | ModelResponse, Refusal |
| Connector Error | Entity | "the call fails with a connector error" | ConnectorError |

Each Target Result is a **CaseExecuted** event: a case was sent to the target (answered, refused or failed) or was not sent. The Progress Listener subscribes to it.

## 3. Analysis sequence

How the analysis objects work together to deliver the main success scenario. The control object drives the work, entities hold the information, and only the boundaries talk to the outside.

Diagram: [UC-003 analysis sequence](diagrams/analysis-sequence.puml)

## 4. Rules the design must keep

These come from the use case's business rules and its scenarios. The design is checked against them.

1. Every case ends with exactly one Target Result, in benchmark order, holding either a model response or a connector error, never both and never neither (AC-003-01, AC-003-02).
2. One call per case. Execute Target never retries; retrying is the connector's job (AC-003-01).
3. A connector error on one case is data about that case. The run goes on (AC-003-02).
4. An auth or quota error stops the run: no later case is sent, and each gets the error naming the cause and the case where it happened (AC-003-03).
5. The listener hears about every case, including failed and not-sent ones, in order (AC-003-04).
6. Only connector errors are caught. Anything else is a bug and reaches the caller unchanged (AC-003-05).
7. A refusal or a cut-off answer is a model response, not an error. Deciding what it means belongs to the evaluation (UC-004, UC-006).
8. Execute Target works with any target. Nothing in it depends on which provider answers.
