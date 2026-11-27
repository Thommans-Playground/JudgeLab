# UC-002 Analysis: Prepare benchmark dataset

> **Draft for review.** Analysis describes *what* has to happen, in the problem's words: no Python, no SDKs, no patterns. The [design](design.md) says how the code does it.

| Field | Value |
|---|---|
| Use case | [UC-002](README.md) |
| Criteria | [UC-002.feature](UC-002.feature) |
| Bounded context | [Benchmark](../../domain/benchmark/README.md) |
| Ontology | [Benchmark](../../ontology/benchmark.md), [TestCase](../../ontology/test-case.md) |

## 1. System sequence diagram

The system is a black box. The diagram shows only what crosses its boundary: a path going in, and a benchmark or an error listing every problem coming back. It is the main success scenario and its extensions, drawn.

![UC-002 system sequence diagram](diagrams/ssd.svg)

Source: [diagrams/ssd.puml](diagrams/ssd.puml)

**System operations** found here:

| Operation | Responsibility | Postcondition |
|---|---|---|
| load benchmark(path) | Read, parse and check a benchmark file, and build the benchmark from it | A benchmark exists with at least one case, unique case ids and no blank fields, cases in file order (AC-002-01, AC-002-03) |
| error(path, problems) | Reject a file that can't be trusted, saying every reason at once | No benchmark exists; the error names the file and lists every problem with its location, in file order (AC-002-02, AC-002-04 to AC-002-08) |

## 2. Analysis classes

Found by reading the use case's nouns and splitting them by role:

- **Boundary:** where the system meets something outside it. Here, the benchmark file.
- **Control:** the use case's logic, the steps of the main flow. One per use case is typical.
- **Entity:** information the problem cares about, which outlives one step.

The Benchmark is an **aggregate**: it and its test cases are created together, checked together and only ever used as a whole. The Benchmark is its root, and its invariants are the rules a file must pass.

![UC-002 analysis classes](diagrams/analysis-classes.svg)

Source: [diagrams/analysis-classes.puml](diagrams/analysis-classes.puml)

| Analysis class | Role | Comes from (use case text) | Ontology concept |
|---|---|---|---|
| Benchmark File Reader | Boundary | "reads the file at the given path" | — |
| Prepare Benchmark | Control | the main success scenario, steps 1 to 5 | Benchmark (the loader) |
| Benchmark | Entity, aggregate root | "returns the benchmark: its id, its name and its test cases" | Benchmark |
| Test Case | Entity, inside the aggregate | "each case holds id, question and expected_answer" | TestCase |
| Problem List | Entity | "every problem … is reported together … in file order" | — (exists only during the load) |
| Benchmark Error | Entity | "an error names the file and lists every problem found" | — |

**Benchmark invariants**, which hold for every Benchmark the system creates:

| Invariant | Broken by | Criterion |
|---|---|---|
| id and name are non-empty strings | extension 3a | AC-002-04 |
| at least one test case | extension 3b | AC-002-07 |
| every case is an object with id, question and expected answer as non-empty strings | extensions 4a, 4b | AC-002-04 |
| no field the schema does not know | extension 4c | AC-002-06 |
| case ids are unique within the benchmark | extension 4d | AC-002-05 |
| cases keep their file order | — (a business rule, not a check) | AC-002-01 |

A Test Case's identity is its id *within its Benchmark*. Two benchmarks may both have a case "c1"; one benchmark may not.

## 3. Analysis sequence

How the analysis objects work together to deliver the main success scenario. The control object drives the work, entities hold the information, and only the boundary talks to the outside.

![UC-002 analysis sequence](diagrams/analysis-sequence.svg)

Source: [diagrams/analysis-sequence.puml](diagrams/analysis-sequence.puml)

## 4. Rules the design must keep

These come from the use case's business rules and its scenarios. The design is checked against them.

1. No model is called for a benchmark that fails to load: loading comes before anything reaches a model.
2. A Benchmark exists only if every invariant holds. There is no half-valid benchmark (AC-002-04 to AC-002-07).
3. Checking does not stop at the first problem. Every problem from steps 3 and 4 is reported in one error, in file order (AC-002-08).
4. A problem that stops the file being read at all (missing file, invalid JSON, top level not an object) is reported on its own, since nothing after it can be checked (AC-002-02).
5. Every problem gives its location, like `cases[1].question`, and the error names the file (AC-002-02, AC-002-04).
6. Unknown fields are errors, not ignored, so a typo can't silently drop an expected answer (AC-002-06).
7. Cases keep their file order (AC-002-01).
