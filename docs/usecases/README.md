# Use Cases

One folder per use case (`UC-###-<slug>/`): its `README.md` holds the flows, its `UC-###.feature` holds the acceptance criteria as Gherkin scenarios tagged `@AC-UUU-NN`, `analysis.md` and `design.md` realise it with OOAD (PlantUML sources in `diagrams/`), and its task files are the use case's **slices**, thin end-to-end pieces that each make some criteria pass. Create both with the `vbench-docs` script (`new UC`, `new T --usecase UC-###`).

## Actors

| Actor | Description |
|---|---|
| Developer | Runs evaluations from the CLI |

## Catalogue

| ID | Name | Primary actor | Requirements | Introduced in | Status |
|---|---|---|---|---|---|
| [UC-001](UC-001-configure-model-connections/) | Configure model connections | Developer | REQ-003, REQ-004, REQ-013 | v0.1 | Draft |
| [UC-002](UC-002-prepare-benchmark-dataset/) | Prepare benchmark dataset | Developer | REQ-001, REQ-002 | v0.1 | Draft |
| [UC-003](UC-003-execute-target-model/) | Execute target model | Developer | REQ-005 | v0.1 | Draft |
| [UC-004](UC-004-evaluate-responses/) | Evaluate responses | Developer | REQ-006, REQ-007, REQ-008 | v0.1 | Draft |
| [UC-005](UC-005-generate-report/) | Generate report | Developer | REQ-009, REQ-010 | v0.1 | Draft |
| [UC-006](UC-006-run-complete-evaluation/) | Run complete evaluation | Developer | REQ-008, REQ-011, REQ-012 | v0.1 | Draft |
