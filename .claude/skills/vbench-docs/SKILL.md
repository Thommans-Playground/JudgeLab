---
name: vbench-docs
description: Manage the repository's engineering docs (requirements REQ, use cases UC, architecture decisions ADR, tasks T as slices of use cases, acceptance criteria AC, test cases TC, ontology concepts, the DDD domain model with bounded contexts, aggregates, entities, value objects and domain events, traceability matrix, release folders) with correct unique IDs and consistent indexes. Use this skill whenever adding, editing, renaming, retiring, or changing the status of a requirement, use case, decision, task, test case, domain concept, bounded context, aggregate, or domain event; planning a release or its tasks; updating traceability; checking docs consistency; or before committing or opening a PR that touches docs/, even if the user just says "add a requirement for X", "log this decision", "new task", or "is the traceability up to date?".
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

Kinds and ID formats: `REQ-001`, `UC-001`, `ADR-001`, `TC-001` (rows in `verification.md`, not files), tasks `T-004-02` (task 02 of UC-004) and acceptance criteria `AC-004-01` (criterion 01 of UC-004). Tasks and criteria are numbered within their use case, with two digits after the use case number. `next` considers every ID ever mentioned, so retired numbers are never reused. `--release` defaults to the latest release folder.

**Use cases and their slices.** A use case is a folder, `docs/usecases/UC-###-<slug>/`. Its `README.md` holds the goal, trigger, flows (main success scenario, extensions), postconditions, business rules and a **Slices** table. Its **acceptance criteria** live next to it in `UC-###.feature`, written in Gherkin: one `Scenario` (or `Scenario Outline`) per criterion, tagged with exactly one `@AC-UUU-NN`. That file is the only place a criterion is defined; everything else refers to it by ID. Tasks are the use case's slices: thin, end-to-end pieces of work that each make some of its criteria pass. They live in the same folder (`T-UUU-NN-<slug>.md`), list the criteria they deliver in their `Delivers` section, and carry a `Release` field. Commands:
- `new UC --title "Prepare dataset"` creates the folder, its README and its `.feature` file.
- `new T --usecase UC-002 --title "JSON loader"` creates a task inside it (e.g. `T-002-03`); `next T --usecase UC-002` just prints the next ID; then add it to the use case's Slices table, the release plan, and `traceability.md`.
- `next AC --usecase UC-004` prints the next free criterion ID.

**Writing a criterion.** Derive criteria from the main flow, each extension, the postconditions, the business rules and any non-functional constraint. Each one is observable (Then describes what a user or caller can see), testable, about one behaviour, unambiguous, and independent of the others; cover the unhappy paths, not just the happy one. Use a `Scenario Outline` with `Examples` when the same rule holds for several inputs.

**Drift.** Clarifying a criterion's wording is fine. Changing what it means is a new criterion: add a new Scenario with the next ID, tag the old one `@retired`, and put `# Superseded by AC-UUU-NN: <reason>` above it. Never reuse or renumber an ID. Move the requirement's `Verified by` entry to the new ID and re-point the tests' markers.

`check` verifies that the feature file is named and titled after its use case, that every Scenario has exactly one criterion tag, that each criterion is defined once and in its own use case, that no markdown file defines criteria (the old `**AC-…**` style), that every `AC-…` mention resolves, and that each task lives in the use case its ID names. It also checks **coverage**: every active criterion is listed by at least one requirement, no requirement lists a retired criterion, and every requirement lists at least one criterion (a warning while it is Draft, an error after).

**Requirements point at criteria.** A requirement's `## Verified by` section lists the IDs (never the text) of the use-case criteria that prove it; one requirement can be verified by criteria in several use cases (e.g. a security requirement). When you add a criterion, add its ID to the requirement(s) it verifies. Tests are marked with criterion IDs (`@pytest.mark.acceptance("AC-004-03")`), so pytest's progress table shows which use cases work.

Ontology concepts aren't numbered; they're named by their canonical term. Use `new concept --title TestCase` (creates `docs/ontology/test-case.md` from `docs/ontology/_template.md`), then add the term to the glossary in `docs/ontology/README.md`; `check` fails until you do. When filling a concept:

- **Related** names the relationship type (`Contains`, `Belongs to`, `Produces`, …), not just the neighbour, and should agree with the domain map in the ontology README.
- **Status** (Draft / Active / Deprecated) tells people whether to build on it. Deprecated concepts point to their replacement under "Not to be confused with".
- **Aliases** and **Code** map other names (provider terms, everyday speech) and the implementing class to the one canonical term.
- **Diagrams** only where they earn their place: an `erDiagram` limited to immediate neighbours for concepts with several relationships, a `stateDiagram-v2` for concepts with a lifecycle. Value objects get none; the whole-system map lives in the ontology README.
- **Modelled in** points to the DDD model(s) that implement the concept (`Context:Model`).

## DDD domain model

`docs/domain/` turns the ontology (what exists) into a design (how it is modelled), one folder per bounded context. Read `docs/domain/README.md` first.

- `new context --title Evaluation` → `docs/domain/evaluation/README.md`; then add the context to the bounded contexts table and context map in `docs/domain/README.md`.
- `new model --context evaluation --title JudgeEvaluation` → aggregate root, entity, value object, or domain service.
- `new event --context evaluation --title EvaluationCompleted` → domain event (past tense).
- Add every model and event to its context's ubiquitous language table.

`check` enforces: each context is listed in the domain README; each model/event is in its context's ubiquitous language; `DDD Type` is one of Aggregate Root, Entity, Value Object, Domain Service, Domain Event; `Bounded Context` matches the folder; every Entity names an Aggregate Root in the same context; every `Ontology` value is a defined ontology concept.

Choosing boundaries, aggregates, and invariants is design work, and in this project it's the user's learning. Help by asking questions and pointing out trade-offs (consistency boundary vs. aggregate size, reference by ID vs. containment, when a value object beats an entity), and propose options rather than deciding. Don't create contexts or models the user hasn't asked for.

## Adding an item

1. `new <KIND> --title "..."`. Use the ID it prints; never pick one yourself.
2. Fill the file from what the user told you. Leave fields you don't know empty or as `<!-- TODO -->` rather than inventing requirements, actors or acceptance criteria: in this project the thinking behind these docs is the user's learning work, so ask or leave space.
3. Add a row to the index the script names (link it as `[ID](file)` where the index is a catalogue).
4. For REQ and T: add or update the row in `docs/traceability.md`.
5. Cross-link related items both ways where the templates have fields for it (e.g. a task's Requirements field and the requirement's row in traceability; a use case's Requirements and the requirement's Use cases).
6. For anything in a release's scope (requirements, use cases, tasks), update that release's `README.md` scope or plan table. A new task also gets a row in its use case's Slices table.
7. Run `check` and fix what it reports before calling the work done.

## Changing or retiring items

- **Never renumber, and never delete an item that has been committed.** Other files, commits and branch names point at it. Set its Status to `Deprecated` (requirements), `Rejected`/`Superseded by ADR-###` (decisions), or `Dropped` (tasks), and say why in its change log.
- **Accepted ADRs are immutable**: to change a decision, create a new ADR that supersedes it and update the old one's status line only.
- When a status changes, update it everywhere it is shown (the item's table, its index row, traceability). Only mark traceability `Verified` when a TC exists and there is test evidence for it; otherwise say what is missing.
- Moving a task to another release: change its `Release` field (the file stays in its use case's folder) and update both release plans. A task never moves between use cases; if its scope changes that much, retire it and create a new one.

## Checking hygiene

Run `check` whenever you finish editing docs, before a docs commit (see `vbench-commit`), and as part of the PR readiness check (see `vbench-pr`). Report errors and warnings to the user with a proposed fix for each; fix mechanical ones (missing index row, typo in a link) directly, but ask before resolving anything that needs a judgement (which of two duplicate IDs to renumber, whether an undefined reference should become a new item).

CI runs the same `check` on pull requests (`.github/workflows/docs-check.yml`), so anything you leave broken will fail the PR.

## Adapting to another repo

The layout lives in the `KINDS` table at the top of `scripts/docids.py`; edit it (folders, index files, kinds) if a repo arranges docs differently, and keep `docs/README.md` in sync.
