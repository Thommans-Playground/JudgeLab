# {{ID}} Design: {{TITLE}}

<!--
Design says HOW the code realises the analysis: real classes, signatures, patterns, and the role of
each in the hexagon (docs/design.md, ADR-001). Draw it before coding the slice; check it afterwards
against an as-built diagram (ADR-002).
-->

| Field | Value |
|---|---|
| Use case | [{{ID}}](README.md) |
| Slices | <!-- task links --> |
| Code | <!-- modules --> |
| Decisions | [ADR-001](../../decisions/ADR-001.md), [ADR-002](../../decisions/ADR-002.md) |

## 1. From analysis to design

| Analysis class | Design element | Hexagon role |
|---|---|---|
| | | |

## 2. Design classes

Diagram: [{{ID}} design classes](diagrams/design-classes.puml)

## 3. Design sequences

Diagram: [{{ID}} design sequence](diagrams/design-sequence.puml)

## 4. Patterns and principles

| Pattern / principle | Where | Why |
|---|---|---|
| | | |

## 5. Rules from the analysis, and where the design keeps them

| Rule | Kept by |
|---|---|
| | |

## 6. Design notes and candidate refactorings

-

## 7. Checking the design against the code (as-built)

```bash
uv run python .claude/skills/vbench-docs/scripts/asbuilt.py sequence "<test node id>" -o <this folder>/diagrams/as-built/sequence.puml
```

A difference is either design drift (update this page and say why) or a code defect (fix the code).
