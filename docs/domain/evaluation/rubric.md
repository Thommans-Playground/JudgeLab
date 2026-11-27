# Rubric

| Field | Value |
|---|---|
| Bounded Context | Evaluation |
| DDD Type | Value Object |
| Aggregate | — |
| Ontology | `Rubric` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `judge.Rubric` (+ `judge.get_rubric`, `judge.RUBRICS`, `judge.SEMANTIC_CORRECTNESS`) |
| Related | Used by: [Judge](judge.md) · Referenced by id from: [JudgeEvaluation](judge-evaluation.md), Reporting:RunInfo |

## Definition

Named instructions that tell the judge what counts as an acceptable answer. It is a strategy expressed as data: changing the rubric changes how answers are graded without changing code.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `id` | `str` | Value Object | yes | v0.1 has one: `"semantic_correctness"`. |
| `instructions` | `str` | Value Object | yes | The judge's system prompt, before the output format is appended. |

## Behaviours (commands)

None on the value. The lookup is a function:

- `get_rubric(rubric_id: str) -> Rubric`: returns the rubric from `RUBRICS`, or raises `JudgeError("unknown rubric ...; known: ...")`.

## Invariants

- Rubrics are chosen by id. An unknown id is rejected with the known ids (AC-004-07).
- `semantic_correctness` accepts an answer that agrees in meaning, ignoring wording, case, punctuation and politeness. It rejects contradictions, added wrong facts, non-answers and refusals.
- The rubric tells the judge to treat everything inside the answer tags as data, never as instructions. This is a prompt-injection defence.

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **Judge** (Evaluation): the service that applies a rubric.
- **Verdict** (Evaluation): the decision a rubric leads to.
- **`judge.OUTPUT_FORMAT`**: the fixed JSON reply format, added to every rubric's instructions. It is not part of the rubric.
