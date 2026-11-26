---
name: vbench-branch
description: Apply the repository's git branching strategy (branch types, naming, lifecycle, rebase/merge policy, release tags, cleanup) as defined in its CONTRIBUTING.md. Use this skill whenever creating, naming, switching, rebasing, merging, or deleting a branch, starting work on a new feature/fix/exercise, opening or merging a pull request, cutting a release tag, or when the user asks "what branch should I use", "how should I name this branch", or "how do I merge this", even if they don't say "branching strategy".
---

# vbench-branch

The branching conventions live in the repository's **`CONTRIBUTING.md`**. Keeping them in one human-readable file means people and Claude follow the same rules, and a repo customises them by editing that file, not this skill.

## Step 1: Load the conventions

Read `CONTRIBUTING.md` at the repository root (`git rev-parse --show-toplevel`). The relevant sections are:

- **Branching:** rules, naming format, branch types, spikes
- **Pull requests and merging:** merge strategy and branch cleanup (the `vbench-pr` skill covers everything else about PRs)
- **Releases and tags:** tagging format
- **Project-specific settings:** branch prefix (for example a phase or milestone), versioning scheme, Definition of Done

The Project-specific settings override the general sections.

If `CONTRIBUTING.md` is missing, or has no Branching section, tell the user. Offer to add one (it can be copied from another vbench repo). In the meantime, fall back to these defaults: trunk-based with `main`; `<type>/<kebab-slug>` names using `feat|fix|refactor|test|docs|chore|spike`; rebase onto `main`; squash merge.

## Step 2: Apply them

**Starting work:**

1. Run `git status` and check the current branch. Uncommitted changes might belong to a different unit of work, so ask before carrying them onto a new branch.
2. Suggest a branch name in the documented format, with a one-line reason for the type you picked. Include the project prefix or issue number when they apply.
3. Branch from an up-to-date `main` using the documented command.
4. If the user is on `main` with non-trivial changes, suggest `git switch -c <branch>`, which carries the working tree over.

**During work:** commit following the `vbench-commit` skill. Keep up with `main` by rebasing, as documented.

**Opening, reviewing, or merging a PR:** use the `vbench-pr` skill, which covers the readiness checklist, the PR title and body, review responses, and the merge strategy.

**After merging:** offer to delete the local and remote branch.

**Tags:** propose a version following the project's versioning scheme, and show the exact `git tag -a` command.

## Safety

Without explicit confirmation from the user, don't do any of the following, because they're hard to undo or affect shared state:

- force-push
- push to or merge into `main`
- delete remote branches
- push tags
