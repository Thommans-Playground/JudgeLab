# Requirements

One file per requirement (`REQ-###.md`): a "shall" statement, its rationale, and **Verified by**, the IDs of the use-case acceptance criteria that prove it. Create new ones with the `vbench-docs` script so IDs stay unique. This index is the catalogue.

> **Draft for review:** the statements and rationale were drafted from the v0.1 plan.

| ID | Title | Type | Priority | Introduced in | Status |
|---|---|---|---|---|---|
| [REQ-001](REQ-001.md) | Load benchmark cases with question and expected answer | Functional | Must | v0.1 | Draft |
| [REQ-002](REQ-002.md) | Validate records, including required fields and unique IDs | Functional | Must | v0.1 | Draft |
| [REQ-003](REQ-003.md) | Configure target and judge independently | Functional | Must | v0.1 | Draft |
| [REQ-004](REQ-004.md) | Support provider, model ID, optional base URL, and API-key environment reference | Functional | Must | v0.1 | Draft |
| [REQ-005](REQ-005.md) | Obtain actual answers from the target model | Functional | Must | v0.1 | Draft |
| [REQ-006](REQ-006.md) | Judge actual answers against question, reference, and rubric | Functional | Must | v0.1 | Draft |
| [REQ-007](REQ-007.md) | Parse and validate verdict and justification | Functional | Must | v0.1 | Draft |
| [REQ-008](REQ-008.md) | Distinguish execution/parse errors from negative verdicts | Functional | Must | v0.1 | Draft |
| [REQ-009](REQ-009.md) | Calculate transparent aggregate metrics and error coverage | Functional | Must | v0.1 | Draft |
| [REQ-010](REQ-010.md) | Persist per-case evidence and execution metadata as JSON | Functional | Must | v0.1 | Draft |
| [REQ-011](REQ-011.md) | Expose end-to-end execution through a CLI | Functional | Must | v0.1 | Draft |
| [REQ-012](REQ-012.md) | Support deterministic tests with fake connectors | Non-functional | Must | v0.1 | Draft |
| [REQ-013](REQ-013.md) | Keep secrets out of logs, errors, and reports | Non-functional | Must | v0.1 | Draft |

## Constraints & assumptions

-

Status values: Draft · Accepted · Implemented · Verified · Deprecated
