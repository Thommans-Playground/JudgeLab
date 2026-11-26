# Contributing

This document defines how we branch, commit, open pull requests, and merge. It is the single source of truth for these conventions. The `vbench-branch`, `vbench-commit`, and `vbench-pr` Claude Code skills read this file rather than duplicating it.

To adopt these conventions in another repository, copy this file plus `.claude/skills/vbench-branch/`, `.claude/skills/vbench-commit/`, and `.claude/skills/vbench-pr/`, then edit only [Project-specific settings](#project-specific-settings).

## Contents

- [Branching](#branching)
- [Commits](#commits)
- [Pull requests and merging](#pull-requests-and-merging)
- [Releases and tags](#releases-and-tags)
- [Project-specific settings](#project-specific-settings)

---

## Branching

We use a lightweight trunk-based model (GitHub Flow): one long-lived branch, `main`, plus short-lived topic branches. We don't use `develop`, `release/*`, or other long-lived branches.

### Rules

1. **`main` is always releasable.** Tests pass, and the code is reviewed and understood. Don't commit directly to `main`, except for trivial typo fixes.
2. **One branch = one unit of work.** One feature slice, one fix, one refactor, one exercise. If scope drifts, finish or park the work and branch again.
3. **Keep branches short-lived.** Aim to merge within a few days. Split large features into vertical slices that can each merge on their own.
4. **Branch from an up-to-date `main`:**
   ```bash
   git switch main && git pull --ff-only && git switch -c <branch>
   ```
5. **Stay current by rebasing:** `git rebase main`. Don't merge `main` into topic branches.

### Naming

Format: `<type>/[<prefix>-]<short-kebab-slug>[-<issue>]`

| Type | Use for | Example |
|---|---|---|
| `feat/` | New capability | `feat/csv-dataset-loader` |
| `fix/` | Bug fix | `fix/score-rounding-14` |
| `refactor/` | Behaviour-preserving restructuring | `refactor/extract-judge-interface` |
| `test/` | Tests only | `test/loader-edge-cases` |
| `docs/` | Documentation | `docs/domain-model` |
| `learn/` | Learning exercises and notes | `learn/dsa-heap-topk` |
| `spike/` | Throwaway exploration, **never merged** | `spike/async-calls` |
| `chore/` | Tooling, CI, dependencies, config | `chore/setup-pytest` |

- Use lowercase and hyphens only, with 2–5 words in the slug.
- Describe the outcome, not the activity: `feat/csv-dataset-loader`, not `feat/working-on-loader`.
- The optional `<prefix>` (for example a milestone or phase) is defined in [Project-specific settings](#project-specific-settings).
- Append the issue number when one exists.

### Spikes

A `spike/` branch is never merged. Record what you learned in the docs through a `docs/` branch, then delete the spike.

---

## Commits

We follow [Conventional Commits](https://www.conventionalcommits.org/).

```text
<type>(<scope>): <subject>

<body: optional, wrapped at 72 chars>

<trailers>
```

### Types

| Type | When |
|---|---|
| `feat` | New capability |
| `fix` | Bug fix |
| `refactor` | Restructuring with no behaviour change |
| `perf` | Performance improvement with no behaviour change |
| `test` | Adding or fixing tests only |
| `docs` | Documentation |
| `learn` | Learning exercises, practice, review notes |
| `build` / `ci` | Packaging, dependencies, pipelines |
| `chore` | Housekeeping that fits nowhere else |

### Scope

The scope is optional but encouraged. It names the area touched and should match a real module or folder. The allowed scopes are listed in [Project-specific settings](#project-specific-settings). If a commit needs several scopes, it's probably too big.

### Subject

- Use the imperative mood: "add", not "added" or "adds". It should complete the sentence *"If applied, this commit will ___"*.
- Lowercase after the colon, no trailing period, and **≤ 72 characters** in total (aim for about 50).
- Be specific: `fix(judge): clamp scores to [0, 1] before aggregation`, not `fix: bug`.

### Body

Add a body whenever the *why* isn't obvious from the subject. It should cover:

- **Why** the change was needed, not a replay of the diff.
- **The design choice** and any alternatives you considered.
- **Concepts applied**, such as algorithms, data structures, or patterns.
- **Breaking changes:** start a paragraph with `BREAKING CHANGE:`, or add `!` after the type or scope (`feat(api)!: ...`).

### Trailers

Separate trailers from the body with a blank line, and put one per line.

| Trailer | When |
|---|---|
| `AI-Assist: L<0-5>` | Every commit with code or learning content (see the scale below) |
| `Refs: #<n>` / `Closes: #<n>` | When an issue exists |
| `Co-Authored-By: <name> <email>` | When someone else, or an AI, wrote part of the content |

**AI-Assist scale.** Record the highest level used for that commit's content:

| Level | Meaning |
|---|---|
| `L0` | Independent, no AI |
| `L1` | Conceptual explanation only |
| `L2` | Progressive hints |
| `L3` | AI code review or debugging guidance |
| `L4` | Reference solution consulted after an independent attempt |
| `L5` | AI-generated code (scaffolding, non-learning-critical) |

Be honest about the level. The history is a record of how independently the work was done, so a wrong level in either direction makes that record useless.

### Examples

```text
feat(benchmark): add runner for multiple-choice suites

Loads a suite, sends each prompt through a connector, and scores
exact-match answers. Results are keyed by item id for O(1) lookup
during report generation.

AI-Assist: L0
```

```text
refactor(judge): extract Judge interface and apply Strategy

The runner branched on judge type with if/elif, so every new judge
meant editing the runner. Judges now implement score() and are
injected.

Considered a function registry; chose Strategy because judges will
need per-instance configuration.

AI-Assist: L2
```

```text
fix(dataset): handle trailing newline in JSONL loader

AI-Assist: L3
Closes: #14
```

### Atomic commits

Each commit should be **one logical change that builds and passes tests on its own**.

- Keep refactors separate from behaviour changes: commit the refactor first (tests still green), then the `feat` or `fix`.
- Keep formatting and renames separate from real edits.
- Put tests in the same commit as the code they verify, or in a `test` commit just before it (TDD).
- Use `git add -p` to split a messy working tree.
- `wip:` commits are fine on your own topic branch. Squash merge cleans them up.

**Never commit** secrets, `.env` files, API keys, large datasets, or generated artifacts.

---

## Pull requests and merging

Open a PR for every topic branch, even on a solo project. It's a review checkpoint and an evidence trail.

**Size:** one unit of work per PR, matching the branch. Aim for a diff a reviewer can read in one sitting (roughly under 400 changed lines, excluding generated files and data). Split anything bigger into stacked or sequential PRs.

**Draft PRs:** open the PR as a draft early if you want feedback on direction. Mark it ready only when the checklist below passes.

**Title:** use the commit format, `<type>(<scope>): <subject>`. With a squash merge, the PR title becomes the commit message on `main`.

**Body:**

```markdown
## What & why
<!-- The problem or requirement, and what this PR changes. Link issues: Closes #N -->

## How it was verified
<!-- Tests added or run (with results), manual checks, benchmarks -->

## Design notes / concepts applied
<!-- Decisions, alternatives considered, DSA/patterns used. "None" is fine -->

## Follow-ups
<!-- Known gaps or deliberately deferred work. "None" is fine -->

## AI assistance
Highest level: L?
```

**Self-review before requesting review:** read your own diff top to bottom as a reviewer would. Remove debug code, commented-out code, and stray files. Make sure every commit follows [Commits](#commits).

**Responding to review:**

- Address each comment with a change or a reply. Don't resolve threads silently.
- Push fixes as new commits during review, so reviewers can see what changed. The squash merge tidies them up.
- If `main` moved, rebase and force-push with `--force-with-lease`. That's safe only on your own topic branch.

**Ready to merge when:**

- Acceptance criteria are met and tests pass.
- Important design decisions are documented.
- Related docs or notes are updated.
- You can explain the change without looking at it.

**Merge strategy:**

- **Squash merge (default).** You get one clean conventional commit per unit of work on `main`.
- **Rebase merge** is for when each commit is meaningful on its own, such as a refactor done in deliberate steps.
- Never force-push `main`. Delete the branch after merging: `git branch -d <b> && git push origin --delete <b>`.

---

## Releases and tags

Use [Semantic Versioning](https://semver.org/) with annotated tags on `main`:

```bash
git tag -a v0.1.0 -m "Milestone 1: <summary>"
```

How versions map to milestones is defined in [Project-specific settings](#project-specific-settings).

---

## Project-specific settings

> Edit this section when copying this file into a new repository. Everything above is meant to stay the same across repos.

**Project:** JudgeLab

**Branch prefix:** use `p<N>` for the roadmap phase when the work belongs to one, for example `feat/p1-benchmark-runner` or `fix/p2-judge-score-rounding`. Leave it out for `learn/`, `chore/`, and cross-cutting work. Phases are listed in the [README roadmap](README.md#project-roadmap).

**Commit scopes:**

- Product: `benchmark`, `dataset`, `judge`, `connector`, `llm-judge`, `orchestrator`, `pipeline`, `guardrail`, `redteam`, `api`, `ui`, `report`
- Learning: `dsa`, `pattern`, `review`
- Repo: `deps`, `ci`, `repo`

Add new scopes as real modules appear.

**AI-Assist trailer:** required. The scale matches the Learning Protocol in the [README](README.md#learning-protocol).

**Versioning:**

- `v0.<phase>.0` when a phase's core capability is complete.
- `v0.<phase>.<n>` for increments within a phase.
- `v1.0.0` is reserved for Phase 9 (the assurance platform).

**Definition of Done:** see the [README](README.md#definition-of-done).
