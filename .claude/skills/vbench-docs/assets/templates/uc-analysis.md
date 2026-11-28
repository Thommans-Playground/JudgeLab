# {{ID}} Analysis: {{TITLE}}

<!--
Analysis says WHAT has to happen, in the problem's words: no Python, no SDKs, no patterns.
Work from the use case's flows and its .feature scenarios. Two diagrams, PlantUML in diagrams/:
{{ID}}-analysis-class.puml and {{ID}}-analysis-sequence.puml.
-->

| Field | Value |
|---|---|
| Use case | [{{ID}}](README.md) |
| Criteria | [{{ID}}.feature]({{ID}}.feature) |
| Bounded context | <!-- link docs/domain/<context>/README.md --> |
| Ontology | <!-- links to the concepts this use case uses --> |

## 1. Analysis class diagram

<!-- Nouns from the use case, split by role: <<boundary>> (meets the outside), <<control>> (the flow), <<entity>> (information). -->

Diagram: [{{ID}}-analysis-class](diagrams/{{ID}}-analysis-class.puml)

| Analysis class | Role | Comes from (use case text) | Ontology concept |
|---|---|---|---|
| | | | |

## 2. Analysis sequence diagram

<!-- How boundary, control and entity objects deliver the main success scenario, with external actors beside
     the boundaries and each extension as an alt branch. -->

Diagram: [{{ID}}-analysis-sequence](diagrams/{{ID}}-analysis-sequence.puml)

**System operations** (what crosses the system boundary):

| Operation | Responsibility | Postcondition |
|---|---|---|
| | | |

## 3. Rules the design must keep

<!-- From business rules and scenarios; cite AC IDs. -->

1.
