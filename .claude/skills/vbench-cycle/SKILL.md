---
name: vbench-cycle
description: Walk the V-model for JudgeLab. Given a use case (UC-UUU), trace it read-only from requirements to verified, understood code and report where every slice stands and what is broken. Given one slice (task T-UUU-NN), find the stage it is at, run that stage's gate (plan, review, qa, tutor) with fresh-context agents, report the results and stop for the user. Invoked deliberately as /vbench-cycle UC-UUU or /vbench-cycle T-UUU-NN; never on several at once.
disable-model-invocation: true
---

# vbench-cycle

The V-model for one slice: down the left side (requirements → domain → architecture → design → plan), across the bottom (TDD), up the right side (unit and integration checks → acceptance → understanding). This skill shows where things stand and moves one slice forward **one gate per run**, stopping wherever the next move is the user's.

**Deliberate and small.** Only run on the one use case or one task the user names. With nothing, or several, ask which one. Never edit `src/` or `tests/`.

**How it runs the other skills.** vbench-plan, vbench-qa and vbench-tutor can only be started by the user, so this skill doesn't call them; it follows their instructions directly:
- **Interactive gates** (plan, tutor) need the user, so run them here: read the skill's `SKILL.md` and follow it.
- **Review gates** (qa, the right-side reviewers) run as fresh-context subagents in parallel. Tell each one which file to follow and the task ID, and nothing about your own view.

## Mode 1: `/vbench-cycle UC-UUU`, trace only

Read-only. Run no reviews and change nothing; this mode is cheap.

Gather:
```bash
python3 .claude/skills/vbench-docs/scripts/docids.py check
python3 .claude/skills/vbench-docs/scripts/archcheck.py
python3 .claude/skills/vbench-qa/scripts/acmap.py --uc UC-UUU
uv run pytest -q --color=no
```
and read: the use case `README.md` (its Slices table: tasks, criteria, status), `plans/` in the use case folder, `diagrams/as-built/`, the requirements whose Verified by lists this use case's criteria, the ontology terms its criteria use, and `learning/tutor-log.md`.

Report the V, top to bottom, one line per level, with ✅ / ⚠ / ❌ and the reason:

```markdown
# V trace: UC-001 Configure model connections, <date>

| Level | State | Detail |
|---|---|---|
| Requirements | ✅ | REQ-003, 004, 005, 012, 013 list UC-001 criteria |
| Use case and criteria | ✅ | 22 criteria; docids check clean |
| Ontology and domain | ⚠ | "base URL" used in AC-001-15 has no ontology entry |
| Architecture | ✅ | archcheck: 0 violations |
| Analysis and design | ⚠ | 4 diagrams; no as-built yet |

| Slice | Delivers | Plan | Code (table) | QA | Tutor | Stage |
|---|---|---|---|---|---|---|
| T-001-03 | AC-001-01 … 10 | none | 3/10 PASS | not run | 0 Go | TDD (no plan) |

**Next:** <the one slice to move, and the command>
```

Mark a level ⚠ only with evidence. Keep each detail to one line.

## Mode 2: `/vbench-cycle T-UUU-NN`, drive one gate

Work out the slice's stage from the evidence, in this order, and run **only the first gate that isn't passed**. Then report and stop.

| # | Stage | How you know it's passed | Gate to run |
|---|---|---|---|
| 1 | **Plan** | `plans/T-UUU-NN.md` exists with Status: Frozen | Follow `.claude/skills/vbench-plan/SKILL.md` for this task (interactive: it asks the user for plan v0 and decisions) |
| 2 | **Build** | every step in the plan has Status: done | No agent. Show the next pending step (Implements, Test first, Prove) and stop: the user writes the test and the code. When the user says a step is done, run its Prove command; if it gives the expected result, append `Status: done · Commit: <short HEAD>` to that step |
| 3 | **Right-side review** | qa and the built-gate reviewers have run since the last step was done, with no open high findings | Spawn in parallel: a subagent told to follow `.claude/skills/vbench-qa/SKILL.md` for T-UUU-NN and return its report; `architecture-reviewer` and `design-test-reviewer` with gate `built`. Merge the results |
| 4 | **Understanding** | `learning/tutor-log.md` has a Go, as the latest row, for every test marked with a delivered criterion | Follow `.claude/skills/vbench-tutor/SKILL.md` for the slice's tests that have no Go yet (interactive) |
| 5 | **Done** | all of the above | Tell the user the slice is complete and what to update: the task's status in the use case Slices table and `docs/traceability.md` (via vbench-docs), and `learning/PROGRESS.md` |

### The loop back

If a gate shows the plan is wrong (a high finding that says a step or decision doesn't hold, a criterion that can't be met as planned, design drift that changes the design), don't continue up the V. Report it and recommend `/vbench-plan T-UUU-NN amend`, which adds superseding steps to the frozen plan. The V is a loop, not a one-way trip.

### Report

End every drive run with:

```markdown
# Cycle: T-UUU-NN <title>, <date>

**Stage:** <n. name> · **Gate run:** <what ran, or none>
**Result:** <passed / findings / waiting on you>

<the gate's findings, merged, most severe first, or the next step to build>

**Your move:** <exactly what the user does next, e.g. "write the test for S-001-03-04, then /vbench-cycle T-001-03">
```
