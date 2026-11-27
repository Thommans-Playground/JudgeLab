# {{ID}} Analysis: {{TITLE}}

<!--
Analysis says WHAT has to happen, in the problem's words: no Python, no SDKs, no patterns.
Work from the use case's flows and its .feature scenarios. Diagrams: PlantUML in diagrams/,
starting with "!include ../../../diagrams/style.iuml". Render with scripts/render_diagrams.py.
-->

| Field | Value |
|---|---|
| Use case | [{{ID}}](README.md) |
| Criteria | [{{ID}}.feature]({{ID}}.feature) |
| Bounded context | <!-- link docs/domain/<context>/README.md --> |
| Ontology | <!-- links to the concepts this use case uses --> |

## 1. System sequence diagram

<!-- The system as a black box: actor(s), "JudgeLab", secondary actors. Messages are system operations. -->

![{{ID}} system sequence diagram](diagrams/ssd.svg)

Source: [diagrams/ssd.puml](diagrams/ssd.puml)

| Operation | Responsibility | Postcondition |
|---|---|---|
| | | |

## 2. Analysis classes

<!-- Nouns from the use case, split by role: <<boundary>> (meets the outside), <<control>> (the flow), <<entity>> (information). -->

![{{ID}} analysis classes](diagrams/analysis-classes.svg)

Source: [diagrams/analysis-classes.puml](diagrams/analysis-classes.puml)

| Analysis class | Role | Comes from (use case text) | Ontology concept |
|---|---|---|---|
| | | | |

## 3. Analysis sequence

<!-- How boundary, control and entity objects deliver the main success scenario. -->

![{{ID}} analysis sequence](diagrams/analysis-sequence.svg)

Source: [diagrams/analysis-sequence.puml](diagrams/analysis-sequence.puml)

## 4. Rules the design must keep

<!-- From business rules and scenarios; cite AC IDs. -->

1.
