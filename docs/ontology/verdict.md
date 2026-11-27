# Verdict

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Modelled in | `Evaluation:Verdict` |
| Aliases | grade, label |
| Related | Held by: `JudgeEvaluation` (exactly 1) · Becomes: `Outcome` (PASS or FAIL) |

## Definition

The judge's decision on one answer: PASS or FAIL. It only exists when the judge gave a well-formed reply.

## Attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| value | enum (PASS, FAIL) | Yes | PASS means the answer is acceptable under the rubric; FAIL means it is not. |

## Invariants

- Only PASS or FAIL is accepted. Letter case and surrounding spaces are ignored, so `fail` reads as FAIL, and a reply wrapped in a Markdown `json` code fence is still read (AC-004-02).
- A verdict is accepted only together with a non-empty justification (AC-004-02).
- Anything else (prose, other words such as "MAYBE", a non-object) gives no verdict at all (AC-004-02, AC-004-03).
- When a verdict exists, it becomes the case's outcome unchanged (AC-006-01).

## Examples

```json
{ "verdict": "FAIL", "justification": "The answer says Lyon, but the capital of France is Paris." }
```

Edge case: `{"verdict": "PARTIAL", "justification": "..."}` is not a verdict. The case becomes ERROR at the judge stage.

## Not to be confused with

- **Outcome**: has a third value, ERROR, for cases with no verdict. Every verdict becomes an outcome, but not every outcome comes from a verdict.
- **Rubric**: the rule. The verdict is one decision made with it.
- **JudgeEvaluation**: the verdict plus its justification, rubric id and the judge's response.
