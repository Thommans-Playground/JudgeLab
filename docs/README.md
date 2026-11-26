# Documentation

Living documents describe the system **as it is now** and evolve across releases. Release folders hold only what belongs to a single release. To see any document as it was at a release, use its tag: `git show v0.1.0:docs/design.md`.

| Path | Contents |
|---|---|
| [requirements/](requirements/) | Requirements catalogue and one file per requirement |
| [usecases/](usecases/) | Actors, use-case catalogue, and one file per use case |
| [ontology/](ontology/) | Problem-space glossary, relationships, and one file per concept |
| [domain/](domain/) | DDD model built on the ontology: bounded contexts, aggregates, entities, value objects, events |
| [design.md](design.md) | Current architecture and components |
| [decisions/](decisions/) | Architecture decision records (ADRs) |
| [verification.md](verification.md) | Test strategy and test cases |
| [traceability.md](traceability.md) | Requirement ↔ use case ↔ task ↔ test, across releases |
| [releases/](releases/) | Per-release plan, tasks, and release report |

**IDs:** `REQ-###` requirements · `UC-###` use cases · `ADR-###` decisions · `TC-###` test cases · `T###` tasks (numbered across all releases, filed under the release that delivers them). Item files are `<ID>.md` or `<ID>-<slug>.md`.

## Keeping IDs and links consistent

Allocate IDs and check the docs with the `vbench-docs` skill's script (Python 3, no dependencies):

```bash
python3 .claude/skills/vbench-docs/scripts/docids.py next REQ                      # next free ID
python3 .claude/skills/vbench-docs/scripts/docids.py new UC --title "Run a suite"  # create from template
python3 .claude/skills/vbench-docs/scripts/docids.py check                         # hygiene report
```

IDs are permanent: never renumber or reuse one; retire items by status instead. CI runs `check` on every pull request that touches `docs/`.
