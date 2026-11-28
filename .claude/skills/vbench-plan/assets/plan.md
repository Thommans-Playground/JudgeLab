# Plan: T-UUU-NN <task title>

| Field | Value |
|---|---|
| Task | [T-UUU-NN](../T-UUU-NN-<slug>.md) |
| Use case | UC-UUU <title> |
| Status | Draft |
| Baseline | `<short commit>`: every `@commit` below refers to the specs as they were at this commit |
| Delivers | AC-UUU-NN, … |
| Plan v0 by | <the user / drafted by the planner and confirmed by the user> |

<!--
How this file works:
- Draft: the planner and the reviewers may change anything.
- Frozen: append-only. Never edit a step or a decision; add a new one that says
  "Supersedes S-… because …". Steps are marked done by adding Status and Commit.
- References are pinned: AC-001-02@05a67e3 means the criterion as worded at that commit.
-->

## Context

<Two to five sentences: what this slice adds, where it sits in the use case, what already exists in the code that it builds on. Link the design sections it realises.>

## Decisions

| ID | Decision | Why | Alternatives rejected | Ref |
|---|---|---|---|---|
| D-UUU-NN-01 | <one line> | <the reason, citing an AC, ADR, rule or design section> | <option: why not> | <ADR-00x / design.md section / —> |

## Steps

One step = one red-green-refactor cycle = one commit. Each step's **Prove** is a command whose expected result shows the step is done.

### S-UUU-NN-01 <imperative title>

- **Implements:** AC-UUU-NN@<commit> (clause: "<the Then/And it satisfies>")
- **Realises:** <design.md section, design class or sequence message>
- **Decision:** D-UUU-NN-01 <or: none>
- **Do:** <the contract: module, function or class signature, behaviour, errors raised. No code.>
- **Test first:** <the failing test to write: Arrange / Act / Assert in one or two lines, and its acceptance marker>
- **Prove:** `uv run pytest -q -k <test name>` → <expected: N passed; table shows AC-… PASS>
- **Depends on:** <S-… or nothing>
- **Status:** pending

## Review

Findings from the review panel and how each was resolved. Filled in by the planner.

| Round | Reviewer | Finding | Severity | Resolution |
|---|---|---|---|---|

## Open questions

<Anything a reviewer raised that needs the user's decision and isn't decided yet. Empty when the plan is frozen.>
