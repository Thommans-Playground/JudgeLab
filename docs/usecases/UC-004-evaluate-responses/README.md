# UC-004: Evaluate responses

| Field | Value |
|---|---|
| Primary actor | Developer |
| Requirements | REQ-006, REQ-007, REQ-008 |
| Introduced in | v0.1 |
| Status | Draft |

## Goal

Structured judge verdicts.

Drafted in the [v0.1 release plan](../../releases/v0.1/README.md); move details here as they are refined.

**Trigger:** a target response is available.

## Preconditions

- A valid test case, target response, rubric and judge connector.

## Main success scenario

1. Assemble the judge request.
2. Invoke the evaluator.
3. Parse its structured output.
4. Validate the verdict.
5. Record the result.

## Extensions / alternate flows

- Invalid judge output.
- Authentication failure.
- Timeout.
- Provider error.

## Postconditions

- A validated judge evaluation or an explicit error record exists.

## Acceptance criteria

<!-- Observable behaviour, one line each: - [ ] **AC-UUU-NN**: ... (UUU = this use case's number). Tests are marked with these IDs. -->

- [ ] **AC-004-01**: Include question, expected answer, actual answer, and rubric in the judge request.
- [ ] **AC-004-02**: Accept only supported verdict values and a nonempty justification.
- [ ] **AC-004-03**: Invalid output becomes `ERROR`, never `FAIL`.
- [ ] **AC-004-04**: Record evaluator provider/model identity.
- [ ] **AC-004-05**: Switching the judge profile does not change benchmark data or the use-case logic.

## Slices

Each slice is a task file in this folder that makes some of the criteria pass.

| Task | Slice | Delivers | Status |
|---|---|---|---|
| [T-004-01](T-004-01-judge-request-builder.md) | Judge request builder | | Todo |
| [T-004-02](T-004-02-verdict-parser.md) | Verdict parser | | Todo |
