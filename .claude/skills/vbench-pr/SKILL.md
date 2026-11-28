---
name: vbench-pr
description: Prepare, open, update, review, and merge pull requests following the repository's PR conventions (title format, body template, size, self-review, readiness checklist / Definition of Done, review responses, merge strategy) as defined in its CONTRIBUTING.md. Use this skill whenever the user wants to open, create, draft, or describe a PR, write a PR title or description, check whether a branch is ready to merge, respond to review comments, update a PR after review, or merge a PR, even if they just say "ship this", "raise a PR", "is this ready?", or "merge it".
---

# vbench-pr

The PR conventions live in the repository's **`CONTRIBUTING.md`**. Keeping them in one human-readable file means people and Claude follow the same rules, and a repo customises them by editing that file, not this skill.

## Step 1: Load the conventions

Read `CONTRIBUTING.md` at the repository root (`git rev-parse --show-toplevel`). The relevant sections are:

- **Pull requests and merging:** size, drafts, title, body template, self-review, responding to review, readiness checklist, merge strategy
- **Commits:** the PR title uses the commit format, and every commit in the PR should follow it
- **Project-specific settings:** scopes, AI-Assist requirement, Definition of Done

If `CONTRIBUTING.md` is missing, or has no PR section, tell the user and offer to add one. In the meantime, fall back to these defaults: a Conventional Commits title; a body with What & why, How it was verified, and Follow-ups; squash merge.

Use the `gh` CLI for GitHub operations. If `gh` is missing or unauthenticated, or the repo has no remote, still produce the title and body as text the user can paste, and say why you couldn't open the PR.

## Step 2: Open a PR

1. **Gather the facts from git, not from memory.** Run these, using the default branch if it isn't `main`:
   - `git status`, to find uncommitted work. If there is any, ask whether it belongs in the PR and use the `vbench-commit` skill to commit it.
   - `git log --format='%h %s%n%b' main..HEAD`, for the commits and their AI-Assist trailers.
   - `git diff --stat main...HEAD` and `git diff main...HEAD`, for what actually changes.
   - Whether the branch is pushed and up to date with its upstream.
2. **Check the branch is suitable.** Don't open a PR from `main`. If the branch name or scope doesn't fit the conventions, mention it (see the `vbench-branch` skill).
3. **Check size and focus.** If the diff is over the documented size, or mixes unrelated concerns, suggest a split before continuing. Big mixed PRs are hard to review and to revert.
4. **Self-review the diff** as a reviewer would. Flag debug prints, commented-out code, TODOs without an issue, comments that restate the code or non-obvious lines missing a *why* comment (see Code comments in CONTRIBUTING.md), stray or generated files, secrets, and commits that break the commit conventions. Report these to the user rather than silently fixing them, since the fix may need their judgment.
5. **Run the readiness checklist** and the Definition of Done. For each item, report met, not met, or unknown, with the evidence. Run the test suite if one exists and quote the result. Don't tick an item you haven't verified. "Unknown" is an honest answer and better than a false tick.
6. **Draft the title and body:**
   - Title: `<type>(<scope>): <subject>`, summarising the whole PR. With a squash merge it becomes the commit message on `main`, so make it specific.
   - Body: fill the documented template. Write *What & why* from the problem being solved, not as a list of commits. Put real commands and results under *How it was verified*. For *AI assistance*, use the highest `AI-Assist` level across the PR's commits. If any commit lacks a trailer, ask the user rather than guess.
7. **Show the title and body to the user** and confirm whether to open it as a draft (the default when checklist items are unmet) or ready for review.
8. **Push and create the PR** once confirmed. Pass the body through a file or heredoc so its formatting survives:
   ```bash
   git push -u origin HEAD
   gh pr create --draft --title "<title>" --body-file - <<'EOF'
   <body>
   EOF
   ```
   Leave out `--draft` when it's ready for review. Return the PR URL.

## Updating a PR and responding to review

- Fetch the review threads (`gh pr view --comments`, and `gh api repos/{owner}/{repo}/pulls/<n>/comments` for inline comments). Summarise them, grouped as must-fix, questions, and nits.
- For each comment, propose a change or a reply. Make code changes as new commits (using `vbench-commit`). Draft replies for the user to approve rather than posting them unprompted.
- If `main` moved, rebase. Force-push only with `--force-with-lease`, only on the topic branch, and only after the user confirms.
- If the scope changed, update the PR body (`gh pr edit --body-file`).

## Merging

1. Re-run the readiness checklist. Confirm CI passes (`gh pr checks`), all review threads are addressed, and the branch is up to date with `main`.
2. Recommend the documented merge strategy. Say so if this PR qualifies for the exception (for example a rebase merge when each commit tells a meaningful step).
3. For a squash merge, the resulting commit message on `main` should follow the commit conventions. Propose it, including the AI-Assist trailer, and pass it with `--subject` and `--body`.
4. Merge only after explicit confirmation: `gh pr merge <n> --squash --delete-branch` (or `--rebase`). Then `git switch main && git pull --ff-only` and delete the local branch.

## Safety

Without explicit confirmation from the user, don't do any of the following, because they're visible to others or hard to undo:

- push
- open, merge, or close a PR
- post review comments or replies
- force-push
- delete branches
