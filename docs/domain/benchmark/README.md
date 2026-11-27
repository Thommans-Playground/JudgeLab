# Benchmark

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Code | `judgelab.benchmark` |
| Responsibility | Test data and its validity: a benchmark either loads whole and valid, or not at all |

## Purpose

This context owns the test data: a named benchmark and its test cases, each a question with the answer we expect. It decides what a *valid* benchmark is, and it reports every problem in a file at once, so the author can fix them in one pass.

It deliberately does **not** know about models, judging or scores. A test case says nothing about who will answer it or how the answer is graded.

This is a **supporting subdomain**. It is specific to JudgeLab and must be right, but it is simple data validation, not where the product's value lies.

## Ubiquitous language

Every model and event file in this folder must have a row here (the docs check enforces this).

| Term | DDD Type | Ontology | Meaning in this context |
|---|---|---|---|
| [Benchmark](benchmark.md) | Aggregate Root | `Benchmark` | A named, ordered collection of test cases that is run as one evaluation. |
| [TestCase](test-case.md) | Entity | `TestCase` | One question and the answer we expect, identified by its id within the benchmark. |
| [BenchmarkLoader](benchmark-loader.md) | Domain Service | `Benchmark` | Builds a valid Benchmark from a JSON file, or raises `BenchmarkError` listing every problem. |

## Relationships with other contexts

| Context | Relationship | Integration (what crosses the boundary) |
|---|---|---|
| [Evaluation](../evaluation/README.md) | Upstream; Evaluation is Conformist | Evaluation takes `Benchmark` and `TestCase` as they are. `TestCase` objects are embedded in `TargetResult` and `CaseResult`. |
| [Reporting](../reporting/README.md) | Upstream; Reporting is Conformist | The report copies the benchmark's id, name and case count, and each case's id, question and expected answer. |
| Application layer (`cli`, `config`) | Not a context | `config` gives the dataset path; `cli.run_command` calls `load_benchmark`. |

## Domain events

| Event | Published / Consumed | Counterpart context |
|---|---|---|
| — | This context publishes no domain events. | — |

## Policies and cross-aggregate rules

- **All or nothing.** A benchmark with any problem is rejected as a whole. No partial benchmark ever reaches a run (AC-002-08).
- **Report every problem at once,** each with its location, such as `cases[1].question` (AC-002-04, AC-002-08).
- **Strict schema.** Unknown fields are errors, so typos are caught (AC-002-06).
- **File order is run order** (AC-002-01).
