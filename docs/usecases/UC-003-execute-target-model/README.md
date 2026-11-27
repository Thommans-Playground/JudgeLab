# UC-003: Execute target model

| Field | Value |
|---|---|
| Primary actor | Developer |
| Requirements | REQ-005 |
| Introduced in | v0.1 |
| Status | Draft |

## Goal

Every test case's question is sent to the target model, and what came back is captured against that case: the answer, or the error that stopped it. A failure on one case must not cost the answers to the others, but a failure that will repeat on every call must stop the run early instead of sending calls that can't succeed.

> **Draft for review.** The flow and the scenarios were drafted from the [v0.1 release plan](../../releases/v0.1/README.md) and the slice's objective. AC-003-01 to 05 keep the meanings the tests are marked with.

**Trigger:** an evaluation run has a loaded benchmark (UC-002) and a target connection (UC-001).

## Preconditions

- A loaded benchmark with at least one test case (UC-002).
- A target connection, chosen by its profile (UC-001).
- Optionally, a progress callback that wants to hear about each case as it finishes.

## Main success scenario

1. The system takes the next test case, in benchmark order.
2. The system sends the case's question to the target, once.
3. The target replies, and the system records a result for the case: the case and the model response.
4. The system calls the progress callback, if there is one, with that result.
5. The system repeats steps 1 to 4 until every case has a result, then returns the results in benchmark order.

## Extensions / alternate flows

- **2a.** The target call fails with a connector error, such as the server failing or a rate limit: the case's result records that error and has no response. The run continues with the next case.
- **2b.** The target rejects the key or is out of credit: the case's result records that error. Every remaining case would fail the same way, so none of them is sent. Each gets a result with no response and the error "not sent: run stopped after ConnectorAuthError on case c2" (or ConnectorQuotaError), naming the cause and the case where it happened.
- **2c.** The target code raises something that is not a connector error, which means a bug: the run stops and the exception reaches the caller unchanged. It is not recorded as a case result.
- **3a.** The target refuses, or its answer is cut off by the length limit: this is still a response, and it is recorded as one. Deciding what it means is left to the evaluation (UC-004, UC-006).

## Postconditions

- Every case in the benchmark has exactly one result, in benchmark order, holding either a model response or a connector error.
- No case was sent to the target more than once.

## Business rules

- One call per case. The runner does not retry; retrying is the connector's job.
- A connector error on one case is data about that case, not a reason to lose the run.
- Auth and quota errors stop the run, because every remaining call would fail the same way.
- Only connector errors are caught. Any other exception is a bug and must stay visible.

## Acceptance criteria

Defined as Gherkin scenarios in [UC-003.feature](UC-003.feature): one Scenario per criterion, tagged with its ID. Tests are marked with the same IDs, so pytest's progress table shows which ones pass.

## Analysis and design

- [Analysis](analysis.md): system sequence diagram, analysis classes (boundary, control, entity) and the analysis sequence, in problem terms.
- [Design](design.md): design classes and sequences in code terms, the patterns used, and how to check the code against them (as-built).

## Slices

Each slice is a task file in this folder that makes some of the criteria pass.

| Task | Slice | Delivers | Status |
|---|---|---|---|
| [T-003-01](T-003-01-target-inference.md) | Target inference | AC-003-01, AC-003-02, AC-003-03, AC-003-04, AC-003-05 | Todo |
