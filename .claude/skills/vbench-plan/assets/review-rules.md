# Rules for every reviewer

These apply to the requirements, domain, architecture and design-test reviewers. Read them before reviewing.

## What you are given

- **One task ID** (T-UUU-NN) and the **gate**: `plan` (before code: review the plan file) or `built` (after code: review the code and tests of that slice against the same sources).
- The plan file path, at `docs/usecases/UC-UUU-<slug>/plans/T-UUU-NN.md`.

You are not given the planner's reasoning, on purpose. Judge the plan and the code against the sources, not against anyone's intentions. If a choice in the plan has no stated reason, that itself is a finding.

## What you must not do

- Don't edit any file. You report; the planner and the user decide and change things.
- Don't review beyond the one task. Mention a problem elsewhere only if this slice depends on it, in one line.
- Don't invent requirements or expected behaviour. If the sources don't say what should happen, report it as a question for the user, not as a defect.
- Don't report style preferences that no source supports.

## Running the mechanical checks first

Before using judgement, run the checks that apply to your lens and read their output:

```bash
python3 .claude/skills/vbench-docs/scripts/docids.py check        # IDs, links, coverage, diagram names
python3 .claude/skills/vbench-docs/scripts/archcheck.py           # imports vs design.md Components
python3 .claude/skills/vbench-qa/scripts/acmap.py --task T-UUU-NN # criteria with their tests
```

Report a failing check as a finding with the check's own message as evidence. Spend your judgement on what the scripts can't see.

## Finding format

Return a short summary line and then a table, most severe first. Every finding needs evidence; a finding without a source you can point at is dropped.

| # | Severity | Rule broken (source) | Evidence | Finding | Proposed fix | Kind |
|---|---|---|---|---|---|---|
| 1 | high | AC-001-02@05a67e3, clause "And it carries the key from …" | plan S-001-03-02 | No step proves the key comes from api_key_env | Add a Test first asserting the authorization header | fix |

- **Severity:** `high` (the slice would be wrong or unverifiable), `medium` (a real gap or inconsistency), `low` (worth fixing, won't break anything).
- **Evidence:** an ID with commit, a plan step ID, or `file:line`.
- **Kind:** `fix` when the right answer follows from the sources (the planner can apply it), or `decision` when it needs the user to choose between options (state the options).

If you find nothing, say so in one line. Don't pad.
