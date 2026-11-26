---
name: vbench-commit
description: Write and make commits following the repository's commit conventions (Conventional Commits types and scopes, subject/body rules, AI-Assist and other trailers, atomic commits, PR titles) as defined in its CONTRIBUTING.md. Use this skill whenever writing, drafting, reviewing, amending, or squashing a commit message, when the user says "commit this", "write a commit message", "stage and commit", or asks how to structure commits or PR titles, even if they don't mention guidelines.
---

# vbench-commit

The commit conventions live in the repository's **`CONTRIBUTING.md`**. Keeping them in one human-readable file means people and Claude follow the same rules, and a repo customises them by editing that file, not this skill.

## Step 1: Load the conventions

Read `CONTRIBUTING.md` at the repository root (`git rev-parse --show-toplevel`). The relevant sections are:

- **Commits:** format, types, subject and body rules, trailers (including the AI-Assist scale), examples, atomic commits
- **Pull requests and merging:** the PR title format
- **Project-specific settings:** allowed scopes, whether the AI-Assist trailer is required

The Project-specific settings override the general sections.

If `CONTRIBUTING.md` is missing, or has no Commits section, tell the user. Offer to add one (it can be copied from another vbench repo). In the meantime, fall back to plain Conventional Commits: `<type>(<scope>): <imperative subject ≤72 chars>`, a body explaining *why*, and one logical change per commit.

## Step 2: Commit workflow

1. **Inspect the real changes:** `git status`, `git diff`, `git diff --staged`. Write the message from the diff, not from memory of the conversation, because the two often differ (forgotten files, unrelated edits).
2. **Check atomicity.** If the changes contain several logical units (for example a refactor mixed with a feature, or formatting mixed with real edits), propose a split into separate commits and confirm with the user before staging.
3. **Check the branch.** If it's `main` and the change isn't trivial, suggest a topic branch first (see the `vbench-branch` skill).
4. **Check for secrets.** Don't stage `.env` files, keys, credentials, large data, or generated artifacts. If any show up, warn the user.
5. **Draft the message:**
   - Pick the type, and a scope from the project's scope list. If no listed scope fits, say so instead of inventing one, and suggest adding it to `CONTRIBUTING.md` if it's a real new module.
   - Write the subject in the imperative mood and within the length limit.
   - Add a body when the *why*, the design choice, or the concepts applied aren't obvious from the subject.
6. **Trailers.** If the project uses `AI-Assist`, decide the level from what actually happened in this session. Ask the user when it's ambiguous (for example they wrote the code but you gave hints earlier), because a wrong level corrupts their progress record. Use `L5` and add a `Co-Authored-By` trailer only when you generated the committed content.
7. **Show the message to the user**, then commit with a heredoc so the formatting survives:
   ```bash
   git commit -F - <<'EOF'
   type(scope): subject

   Body.

   AI-Assist: L2
   EOF
   ```

## Reviewing or rewording existing commits

When asked to review commit messages, check each one against the documented rules and suggest corrected versions.

On a local, unpushed topic branch, rewording is fine with `git commit --amend`, or a non-interactive rebase such as `git rebase --exec` or `GIT_SEQUENCE_EDITOR`. Never amend or rewrite commits that have been pushed or are on `main` without explicit confirmation.

## Safety

Without explicit confirmation from the user, don't do any of the following:

- push
- amend published commits
- rewrite shared history
