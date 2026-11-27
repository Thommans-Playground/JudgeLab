# Refusal

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Modelled in | `Model Access:ModelResponse` (its `refusal` field) |
| Aliases | declined answer |
| Related | Carried by: `ModelResponse` · Judged by: `JudgeModel` (as the actual answer) |

## Definition

A model's explicit decision not to answer. It is a real outcome of the call, not an error: the target did reply, and the judge decides whether refusing was right.

## Attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| message | text | Yes | The model's refusal text, e.g. "I can't help with that." |

## Invariants

- A refusal is returned as a response with no text and the refusal message; no error is raised (AC-001-04).
- A target's refusal is sent to the judge as the answer, marked `[refused] <message>` (AC-006-04).
- A judge that refuses to evaluate gives no verdict, so the case is ERROR at the judge stage (AC-004-03).

## Examples

How a target refusal appears in the report:

```json
{
  "id": "gk-004",
  "outcome": "FAIL",
  "actual_answer": null,
  "refusal": "I can't help with that.",
  "verdict": "FAIL",
  "justification": "The model refused to answer a harmless question.",
  "error": null
}
```

## Not to be confused with

- **ConnectorError**: the call failed and we do not know what the model would have said. With a refusal we know exactly what it said.
- **Verdict FAIL**: a refusal is not automatically a FAIL. The `semantic_correctness` rubric tells the judge a refusal is incorrect, but a different rubric could reward refusing a harmful question.
- **Judge refusal**: when the judge (not the target) refuses, there is no verdict, and the case is ERROR.
