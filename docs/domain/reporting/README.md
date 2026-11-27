# Reporting

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Code | `judgelab.report` |
| Responsibility | Publishing a finished run as reviewable evidence: one JSON report, version "1" |

## Purpose

This context turns a finished run into a document a human can review and a tool can read. It records what was run, with what, and when, the summary, and every case's evidence. It also writes that document to disk with a unique, time-stamped name.

It deliberately does **not** decide outcomes or compute scores. It copies them from Evaluation. It never holds or prints a secret.

This is a **supporting subdomain**. The report format is ours and reviewers depend on it, but building it is a straightforward mapping.

## Ubiquitous language

Every model and event file in this folder must have a row here (the docs check enforces this).

| Term | DDD Type | Ontology | Meaning in this context |
|---|---|---|---|
| [Report](report.md) | Value Object | `Report` | The JSON document (`report_version` "1") for one run. A Published Language. |
| [RunInfo](run-info.md) | Value Object | `EvaluationRun` | The run's identity, times, benchmark, rubric id and connections, as needed for the report. |

## Relationships with other contexts

| Context | Relationship | Integration (what crosses the boundary) |
|---|---|---|
| [Evaluation](../evaluation/README.md) | Conformist (downstream) | Reads `CaseResult`, `Outcome`, `JudgeEvaluation` and `Summary` as they are. |
| [Model Access](../model-access/README.md) | Conformist (downstream) | Reads `ModelResponse` fields and a connector's `provider`, `model` and `base_url`. |
| [Benchmark](../benchmark/README.md) | Conformist (downstream) | Reads the benchmark's id, name and cases. |
| Reviewers (people and tools reading the JSON) | Published Language (this context is upstream) | The report JSON, `report_version` "1". Any breaking change needs a new version. |
| Application layer (`cli`) | Not a context | `cli.run_command` builds `RunInfo`, calls `build_report` and `write_report`, and prints the path. |

## Domain events

| Event | Published / Consumed | Counterpart context |
|---|---|---|
| — | No events published or consumed in v0.1. The CLI calls this context after the run. | — |

## Policies and cross-aggregate rules

- **No secrets, ever.** The report contains neither a key nor the name of its variable (AC-005-06).
- **Evidence for every case:** question, expected and actual answer, refusal, verdict, justification, both calls' metadata, and the error (AC-005-04).
- **Provenance:** run id, start and finish times, JudgeLab version, benchmark, rubric, and both connections (AC-005-05).
- **Stable file names:** UTF-8 JSON named `run-<UTC start>-<first 8 of run id>.json` (AC-005-07).
