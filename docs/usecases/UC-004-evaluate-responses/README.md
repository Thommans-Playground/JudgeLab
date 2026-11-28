# UC-004: Evaluate responses

| Field | Value |
|---|---|
| Primary actor | Developer |
| Requirements | REQ-003, REQ-006, REQ-007, REQ-008 |
| Introduced in | v0.1 |
| Status | Draft |

## Goal

Every answer from the target is judged against its question, its expected answer and a rubric, so that each case ends with a trustworthy verdict (PASS or FAIL) or an explicit error. A judge whose reply cannot be trusted tells us nothing about the target, so it must never turn into a FAIL.

> **Draft for review.** The flow and the scenarios were drafted from the [v0.1 release plan](../../releases/v0.1/README.md), whose AC-004-01 to 05 they keep.

**Trigger:** the target model has answered a test case (UC-003).

## Preconditions

- A valid test case with its question and expected answer (UC-002).
- The target's answer, or its refusal.
- A judge connection (UC-001) and a rubric, chosen by id.

## Main success scenario

1. The system builds the judge's prompt from the question, the expected answer and the actual answer, each in its own tag.
2. The system sends the prompt to the judge model, with the rubric and the required output format as instructions.
3. The judge replies with a JSON object holding a verdict and a justification.
4. The system validates the reply: the verdict is PASS or FAIL and the justification is not empty.
5. The system records the evaluation: verdict, justification, rubric id, and the judge's requested and served model.

## Extensions / alternate flows

- **2a.** The judge can't be reached, rejects the key, is out of credit or fails on the server: no verdict is produced, and the case is ERROR. An auth or quota failure means every remaining judgement would fail too, so judging stops (UC-006).
- **3a.** The judge refuses to evaluate, or its reply is cut off by the length limit: no verdict, ERROR.
- **4a.** The reply is not valid JSON, is not an object, has an unsupported verdict or has no justification: no verdict, ERROR, never FAIL.

## Postconditions

- Either a validated evaluation exists, with the judge's identity, or an explicit judge error explains why there is none.

## Business rules

- A judgement we can't read or trust is an ERROR, never a FAIL.
- The answer being judged is data, never instructions: it is kept inside its own tag, and the rubric says so.

## Acceptance criteria

Defined as Gherkin scenarios in [UC-004.feature](UC-004.feature): one Scenario per criterion, tagged with its ID. Tests are marked with the same IDs, so pytest's progress table shows which ones pass.

## Analysis and design

- [Analysis](analysis.md): analysis class and sequence diagrams (boundary, control, entity), in problem terms.
- [Design](design.md): design class and sequence diagrams in code terms, the patterns used, and how to check the code against them (as-built).

## Slices

Each slice is a task file in this folder that makes some of the criteria pass.

| Task | Slice | Delivers | Status |
|---|---|---|---|
| [T-004-01](T-004-01-judge-request-builder.md) | Judge request builder | AC-004-01, AC-004-04, AC-004-06, AC-004-07 | Todo |
| [T-004-02](T-004-02-verdict-parser.md) | Verdict parser | AC-004-02, AC-004-03 | Todo |
