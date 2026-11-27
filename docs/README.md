# Documentation

Living documents describe the system **as it is now** and evolve across releases. Release folders hold only what belongs to a single release. To see any document as it was at a release, use its tag: `git show v0.1.0:docs/design.md`.

| Path | Contents |
|---|---|
| [requirements/](requirements/) | Requirements catalogue and one file per requirement |
| [usecases/](usecases/) | Actors, the use-case catalogue, and one folder per use case holding its flows (`README.md`), its acceptance criteria as Gherkin scenarios (`UC-###.feature`), its OOAD analysis and design (`analysis.md`, `design.md`, PlantUML in `diagrams/`) and its tasks (its slices) |
| [ontology/](ontology/) | Problem-space glossary, relationships, and one file per concept |
| [domain/](domain/) | DDD model built on the ontology: bounded contexts, aggregates, entities, value objects, events |
| [design.md](design.md) | How the design is derived (requirements → ontology → DDD → OOAD), the hexagonal architecture, components and patterns |
| [diagrams/](diagrams/) | System-level PlantUML diagrams and the shared `style.iuml` |
| [decisions/](decisions/) | Architecture decision records (ADRs) |
| [verification.md](verification.md) | Test strategy and test cases |
| [traceability.md](traceability.md) | Requirement ↔ use case ↔ task ↔ test, across releases |
| [releases/](releases/) | Per-release plan and release report |

**IDs:** `REQ-###` requirements · `UC-###` use cases · `ADR-###` decisions · `TC-###` test cases · `T-UUU-NN` tasks (task NN of use case UC-UUU, e.g. `T-001-03`; each is a slice of that use case, lives in its folder and has a Release field) · `AC-UUU-NN` acceptance criteria (a tagged Scenario in use case UC-UUU's `.feature` file, e.g. `@AC-004-01`; requirements list the criteria that verify them under `Verified by`, and a criterion whose meaning changes is retired and superseded, never edited). Item files are `<ID>.md` or `<ID>-<slug>.md`; use cases are folders `UC-###-<slug>/`.

## Keeping IDs and links consistent

Allocate IDs and check the docs with the `vbench-docs` skill's script (Python 3, no dependencies):

```bash
python3 .claude/skills/vbench-docs/scripts/docids.py next REQ                      # next free ID
python3 .claude/skills/vbench-docs/scripts/docids.py new UC --title "Run a suite"  # create from template
python3 .claude/skills/vbench-docs/scripts/docids.py check                         # hygiene report
```

IDs are permanent: never renumber or reuse one; retire items by status instead. CI runs `check` on every pull request that touches `docs/`.

## Diagrams

UML diagrams are PlantUML sources (`.puml`), linked from the pages that explain them ([ADR-002](decisions/ADR-002.md)). Read them with a PlantUML preview, e.g. the VS Code PlantUML extension (Alt+D). `docids.py check` verifies that each one is well formed and that its `!include` resolves. To export SVGs (optional, needs PlantUML installed), run `python3 .claude/skills/vbench-docs/scripts/render_diagrams.py`.

To compare a design with the code, generate as-built diagrams from a traced test or from the modules:

```bash
uv run python .claude/skills/vbench-docs/scripts/asbuilt.py sequence "tests/test_judge.py::<test>" -o <uc>/diagrams/as-built/sequence.puml
uv run python .claude/skills/vbench-docs/scripts/asbuilt.py classes judgelab.judge -o <uc>/diagrams/as-built/classes.puml
```
