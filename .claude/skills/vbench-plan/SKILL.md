---
name: vbench-plan
description: Plan one slice (task T-UUU-NN) down the left side of the V. Takes the user's plan v0, completes it against the requirements, criteria, ontology, DDD, OOAD design, ADRs and existing code, has a panel of fresh-context reviewers (requirements, domain, architecture, design-test) check it, rectifies their findings with the user's decisions, and freezes it as an append-only plan of decisions and test-first steps. Invoked deliberately as /vbench-plan T-UUU-NN, or /vbench-plan T-UUU-NN amend to add superseding steps to a frozen plan.
disable-model-invocation: true
---

# vbench-plan

A slice's plan is the bridge between the left side of the V (what and why) and TDD (how, proved). It records the decisions made for the slice at that point in time and the steps to build it, each with a failing test first and a command that proves it done. Once frozen it is append-only, so it stays an honest history.

**One slice, deliberately.** Run only on the single task the user names. If they give none, several, or a use case, ask which one task, suggesting the one in progress.

**The decisions are the user's.** The user is learning to design. The planner completes and checks the user's thinking, it doesn't replace it, so start from the user's plan v0 and bring every real trade-off back to them. Never edit `src/` or `tests/`; the only file this skill writes is the plan.

## Step 1: Read the slice and its sources

The plan lives at `docs/usecases/UC-UUU-<slug>/plans/T-UUU-NN.md` (one per task).

- If it exists and is **Frozen**, this is an amendment: go to Step 7.
- If it exists as a **Draft**, continue from it.

Read, for this task only:
- the task file (Objective, `## Delivers`, Approach) and the use case `README.md` (flows, extensions, rules);
- the delivered scenarios: `python3 .claude/skills/vbench-qa/scripts/acmap.py --task T-UUU-NN`;
- the requirements that list them (`## Verified by`), the ontology terms they use, and the owning context in `docs/domain/`;
- the use case's `analysis.md`, `design.md` and four diagrams; `docs/design.md` (Components); the ADRs;
- the existing code and tests the slice builds on.

Run `docids.py check`, `archcheck.py` and `uv run pytest -q` and note anything already broken.

## Step 2: Plan v0 from the user

If there is no draft, ask the user for their plan v0 in their own words: a few bullets on the order they'd build it, the main decisions they see, and anything they're unsure of. Wait for it.

If the user explicitly asks you to draft v0 instead, do it, record **Plan v0 by: drafted by the planner**, and mark every decision **proposed** until the user confirms it in Step 5.

## Step 3: Complete the plan

Write the plan from `.claude/skills/vbench-plan/assets/plan.md`. Keep the user's order and decisions unless a source contradicts them; where it does, keep theirs and add an Open question explaining the conflict.

- **Baseline:** `git rev-parse --short HEAD`. Pin every AC reference to it (`AC-001-02@05a67e3`).
- **Decisions:** one row each, with the why citing a source. A decision that affects more than this slice, or is expensive to reverse, is flagged as an ADR candidate.
- **Steps:** one red-green-refactor cycle each, in dependency order, numbered `S-UUU-NN-01`, `-02`, … Each names the clause it implements, the design element it realises, the contract to build (no code), the failing test to write first, and a Prove command with its expected result.
- Every clause and Examples row of every delivered scenario is covered by some step.

## Step 4: Review panel, fresh context

Spawn the reviewers **in parallel**, as subagents, each with only the task ID, the gate `plan` and the plan path. Don't pass your reasoning or the conversation; the point is that they judge the plan against the sources without your framing.

- **Full panel** (default): `requirements-reviewer`, `domain-reviewer`, `architecture-reviewer`, `design-test-reviewer`.
- **Light panel** for a small slice that touches no boundary and adds no domain concept (say so and why): `requirements-reviewer` and `design-test-reviewer`.

## Step 5: Rectify, at most two rounds

Merge the findings, removing duplicates, and record each in the plan's Review table.

- **Kind `fix`:** apply it to the plan.
- **Kind `decision`:** bring it to the user with the options and the reviewer's evidence, one question at a time or grouped with AskUserQuestion, and record the choice as a Decision row.
- A finding you think is wrong: keep it in the table with your reason, and let the user rule on it.

Then re-run only the reviewers whose findings changed the plan, once. If findings remain after the second round, they go to the user as Open questions. Don't loop further.

## Step 6: Freeze

When there are no Open questions and the user agrees, set **Status: Frozen**. Summarise for the user: the decisions, the steps (one line each), the ADR candidates, and the first step to start with. Suggest `/vbench-cycle T-UUU-NN` to track it.

## Step 7: Amend a frozen plan

When TDD, vbench-qa, vbench-tutor or a reviewer shows the frozen plan is wrong, the plan is not edited. Add new Decision rows and new steps that say **Supersedes S-… because …**, pinned to the current HEAD, and review just the new steps with the reviewers whose lens they touch. Update the design or criteria first (vbench-docs) if the change is to them.

## Record

Planning is design guidance: a commit containing the plan records the AI-Assist level from the user's involvement (L2 when the user wrote v0 and made the decisions; L5 if the planner drafted it).
