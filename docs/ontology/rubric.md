# Rubric

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Modelled in | `Evaluation:Rubric` |
| Aliases | grading instructions, criteria |
| Related | Used by: `EvaluationRun` (1 per run) · Followed by: `JudgeModel` · Referenced by: `JudgeEvaluation` (rubric id) |

## Definition

Named instructions telling the judge what counts as an acceptable answer. In v0.1 there is one rubric, `semantic_correctness`: the answer must agree in meaning with the expected answer.

## Attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| id | text | Yes | The name a config uses to choose it, e.g. `semantic_correctness`. |
| instructions | text | Yes | What the judge must check. Sent to the judge as instructions, followed by the required reply format. |

## Invariants

- Rubrics are chosen by id; an unknown id is rejected, and the error lists the known ones (AC-004-07).
- The rubric reaches the judge as instructions, not as part of the answer being judged (AC-004-01, AC-004-06).
- Every judgement records the id of the rubric used (AC-004-04).
- A run uses one rubric for every case, and the report records its id (AC-005-05).

## Examples

```yaml
benchmark:
  dataset: benchmarks/sample.json
  rubric: semantic_correctness
```

In the report: `"rubric": "semantic_correctness"`.

Edge case: `rubric: exact_match` is rejected before the run starts with `unknown rubric 'exact_match'; known: semantic_correctness`.

## Not to be confused with

- **Verdict**: the rubric is the rule; a verdict is the judge's decision after applying it to one answer.
- **Expected answer**: belongs to one test case. The rubric applies to every case in the run.
