# Domain Ontology

The shared vocabulary of JudgeLab: one canonical name per concept, used the same way in conversation, docs, and code.

- One file per concept, named after the canonical term in kebab-case (`test-case.md` for `TestCase`); copy [_template.md](_template.md).
- Every concept file must have a row in the glossary below (the docs check enforces this).
- Put per-concept diagrams in the concept file, limited to its immediate neighbours. The whole-system map belongs here.

## Glossary

| Term | Definition (one line) | Aliases | Status | Introduced in |
|---|---|---|---|---|
| | | | | |

Status values: Draft · Active · Deprecated

## Domain map

<!--
Whole-system view of how the concepts relate, with cardinality.
Keep it in sync with each concept's "Related" field. Mermaid erDiagram or classDiagram both render on GitHub.
-->

## Cross-concept invariants

<!-- Rules that span several concepts, e.g. "every JudgeEvaluation references the EvaluationRubric used for it". Single-concept rules go in that concept's file. -->

-
