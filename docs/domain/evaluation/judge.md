# Judge

| Field | Value |
|---|---|
| Bounded Context | Evaluation |
| DDD Type | Domain Service |
| Aggregate | — |
| Ontology | `JudgeModel` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `judge.Judge` (uses `judge.build_judge_prompt`, `judge.parse_verdict`; raises `judge.JudgeError`) |
| Related | Uses: Model Access:ModelConnector, [Rubric](rubric.md) · Produces: [JudgeEvaluation](judge-evaluation.md) |

## Definition

The service that asks the judge model whether one actual answer is correct for one test case, under one rubric. It accepts only a well-formed verdict. Anything else is a `JudgeError`, which the run turns into ERROR.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `connector` | `connectors.ModelConnector` | Value Object | yes | The judge model's connector, injected. |
| `rubric` | `judge.Rubric` | Value Object | yes | The grading instructions, injected. |
| `instructions` | `str` | Value Object | yes | `rubric.instructions` plus `OUTPUT_FORMAT`, built once. |

The object holds only configuration, so it is stateless in the DDD sense.

## Behaviours (commands)

- `Judge.evaluate(case: TestCase, actual_answer: str) -> JudgeEvaluation`: builds the prompt, calls the judge model with the instructions, rejects a refusal or truncated reply, parses the verdict. Raises `JudgeError`.
- `build_judge_prompt(case: TestCase, actual_answer: str) -> str`: puts the question, expected answer and actual answer in `<question>`, `<expected_answer>` and `<actual_answer>` tags.
- `parse_verdict(text: str) -> tuple[Verdict, str]`: strips an optional code fence, parses JSON, checks the verdict and justification. Raises `JudgeError`.

## Invariants

- The judge sees the question, the expected answer and the actual answer, under the rubric's instructions (AC-004-01).
- Only a supported verdict with a non-empty justification is accepted (AC-004-02).
- A failed call, a judge refusal, a truncated reply or a malformed reply raises `JudgeError`. A connector failure is kept as `__cause__`, so the run can tell an auth or quota error apart (AC-004-03, AC-006-03).
- The verdict records which judge model produced it (AC-004-04).
- Switching the judge is a configuration change only, because the connector is injected (AC-004-05).
- Instructions reach every provider in its own way (AC-004-06).

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **`JudgeModel`** (ontology): the model itself. Judge is the service that talks to it.
- **Model Access:ModelConnector**: knows how to call a model, not how to grade.
- **JudgeEvaluation** (Evaluation): the result of judging.
