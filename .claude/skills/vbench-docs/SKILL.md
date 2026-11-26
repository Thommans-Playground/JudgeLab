---
name: vbench-docs
description: Manage the repository's engineering docs (requirements REQ, use cases UC, architecture decisions ADR, release tasks T, test cases TC, ontology concepts, traceability matrix, release folders) with correct unique IDs and consistent indexes. Use this skill whenever adding, editing, renaming, retiring, or changing the status of a requirement, use case, decision, task, test case, or domain concept; planning a release or its tasks; updating traceability; checking docs consistency; or before committing or opening a PR that touches docs/, even if the user just says "add a requirement for X", "log this decision", "new task", or "is the traceability up to date?".
---

# vbench-docs

The `docs/` tree is a set of linked records: requirements, use cases, decisions, tasks and test cases reference each other by ID, and indexes plus `traceability.md` tie them together. The value of that web depends on IDs being unique and permanent and on every cross-reference being real. Get them from the bundled script, not by counting files, because a miscount or reused ID silently corrupts history in commits, branches and old releases.

## Step 1: Load the conventions

Read `docs/README.md` (layout, ID scheme), plus the index README of whichever area you are touching. If the repo has no `docs/README.md`, tell the user and describe the expected layout from the script's `KINDS` table.

## The script

`scripts/docids.py` (Python 3, standard library only, runs from anywhere in the repo):

| Command | Does |
|---|---|
| `python3 <skill>/scripts/docids.py next REQ` | Print the next free ID for a kind |
| `… new REQ --title "Load benchmark cases" [--release v0.1]` | Allocate the ID and create the file from the template in `assets/templates/` |
| `… list [KIND]` | Show defined IDs and their files |
| `… check [--strict]` | Report duplicates, heading/filename mismatches, items missing from their index, references to undefined IDs, broken relative links; warn on REQ/T absent from traceability |

Kinds and ID formats: `REQ-001`, `UC-001`, `ADR-001`, `T001` (tasks, under `releases/<version>/tasks/`, numbered across all releases), `TC-001` (rows in `verification.md`, not files). Item files may carry a slug: `T001-connection-profile.md`. `next` considers every ID ever mentioned, so retired numbers are never reused. `--release` defaults to the latest release folder.

Ontology concepts aren't numbered; they're named by their canonical term. Use `new concept --title TestCase` (creates `docs/ontology/test-case.md` from `docs/ontology/_template.md`), then add the term to the glossary in `docs/ontology/README.md`; `check` fails until you do. When filling a concept:

- **Related** names the relationship type (`Contains`, `Belongs to`, `Produces`, …), not just the neighbour, and should agree with the domain map in the ontology README.
- **Status** (Draft / Active / Deprecated) tells people whether to build on it. Deprecated concepts point to their replacement under "Not to be confused with".
- **Aliases** and **Code** map other names (provider terms, everyday speech) and the implementing class to the one canonical term.
- **Diagrams** only where they earn their place: an `erDiagram` limited to immediate neighbours for concepts with several relationships, a `stateDiagram-v2` for concepts with a lifecycle. Value objects get none; the whole-system map lives in the ontology README.

## Adding an item

1. `new <KIND> --title "..."`. Use the ID it prints; never pick one yourself.
2. Fill the file from what the user told you. Leave fields you don't know empty or as `<!-- TODO -->` rather than inventing requirements, actors or acceptance criteria: in this project the thinking behind these docs is the user's learning work, so ask or leave space.
3. Add a row to the index the script names (link it as `[ID](file)` where the index is a catalogue).
4. For REQ and T: add or update the row in `docs/traceability.md`.
5. Cross-link related items both ways where the templates have fields for it (e.g. a task's Requirements field and the requirement's row in traceability; a use case's Requirements and the requirement's Use cases).
6. For anything in a release's scope (requirements, use cases, tasks), update that release's `README.md` scope or plan table.
7. Run `check` and fix what it reports before calling the work done.

## Changing or retiring items

- **Never renumber, and never delete an item that has been committed.** Other files, commits and branch names point at it. Set its Status to `Deprecated` (requirements), `Rejected`/`Superseded by ADR-###` (decisions), or `Dropped` (tasks), and say why in its change log.
- **Accepted ADRs are immutable**: to change a decision, create a new ADR that supersedes it and update the old one's status line only.
- When a status changes, update it everywhere it is shown (the item's table, its index row, traceability). Only mark traceability `Verified` when a TC exists and there is test evidence for it; otherwise say what is missing.
- Moving a task to another release: move the file to that release's `tasks/` folder (keeping its ID) and update both release READMEs.

## Checking hygiene

Run `check` whenever you finish editing docs, before a docs commit (see `vbench-commit`), and as part of the PR readiness check (see `vbench-pr`). Report errors and warnings to the user with a proposed fix for each; fix mechanical ones (missing index row, typo in a link) directly, but ask before resolving anything that needs a judgement (which of two duplicate IDs to renumber, whether an undefined reference should become a new item).

CI runs the same `check` on pull requests (`.github/workflows/docs-check.yml`), so anything you leave broken will fail the PR.

## Adapting to another repo

The layout lives in the `KINDS` table at the top of `scripts/docids.py`; edit it (folders, index files, kinds) if a repo arranges docs differently, and keep `docs/README.md` in sync.
