# Design

How JudgeLab is built, from the outside in. It describes v0.1 as the reference solution builds it.

> **Draft for review.**

## How the design was derived

Each layer is derived from the one above it, and checked by the layer opposite it in the V-model:

| Step | Artefact | Where | Checked by |
|---|---|---|---|
| 1. Requirements | REQ statements, use cases, Gherkin criteria | [requirements/](requirements/), [usecases/](usecases/) | Acceptance tests (marked with AC IDs) |
| 2. Ubiquitous language | Ontology: one meaning per word, found by noun/verb analysis of the use cases | [ontology/](ontology/) | Review: every use-case noun maps to a concept |
| 3. Strategic DDD | Bounded contexts and the context map | [domain/](domain/) | Review: each concept has one owning context |
| 4. Tactical DDD = OOAD analysis | Aggregates, entities, value objects, events; per use case: system sequence diagram, BCE analysis classes and analysis sequence | [domain/](domain/), `usecases/*/analysis.md` | Review against the use-case flows |
| 5. Architecture | Hexagon: core, ports, adapters | this page, [ADR-001](decisions/ADR-001.md) | Contract tests on every adapter |
| 6. OOAD design | Per use case: design classes, design sequences, patterns | `usecases/*/design.md` | As-built diagrams from traced tests ([ADR-002](decisions/ADR-002.md)) |
| 7. Code | `src/judgelab/` | | Unit tests |

The work isn't done top-down once for the whole system. Steps 2 and 3 are cheap and cross-cutting, so they cover all use cases. Steps 4 and 6 are done per use case, just before its slices are built.

## Context

![System context](diagrams/system-context.svg)

Source: [diagrams/system-context.puml](diagrams/system-context.puml)

The developer runs one command. JudgeLab reads a YAML config and a JSON benchmark, and reads each API key from the environment variable the config names. It asks the target model each question and has the judge model evaluate every answer, then writes a JSON report.

## Architecture

Hexagonal (ports and adapters), as decided in [ADR-001](decisions/ADR-001.md):

![Ports and adapters](diagrams/hexagon.svg)

Source: [diagrams/hexagon.puml](diagrams/hexagon.puml)

- **Core:** the domain rules. What a valid benchmark is, how a judge's reply becomes a verdict, when a case is ERROR, and how a run is scored. No SDK, file or YAML code.
- **Driven port:** `ModelConnector`. The core asks for an answer and gets JudgeLab's own `ModelResponse` or `ConnectorError` back.
- **Adapters:** one per provider, plus a fake for tests. Each translates its SDK's types and errors (an anti-corruption layer).
- **Driving adapter and composition root:** the CLI builds everything from the config and injects it.
- **Edge I/O without ports (v0.1):** reading the benchmark and the environment, writing the report, and the clock. Each gets a port once it needs a second implementation.

## Bounded contexts and code

| Context | Responsibility | Code |
|---|---|---|
| [Model Access](domain/model-access/README.md) | Reach foundation models: profiles, credentials, connectors, responses, errors | `judgelab.connectors` |
| [Benchmark](domain/benchmark/README.md) | Test data and its validity | `judgelab.benchmark` |
| [Evaluation](domain/evaluation/README.md) (core) | Ask, judge, decide each case's outcome, score the run | `judgelab.runner`, `judgelab.judge`, `judgelab.scoring` |
| [Reporting](domain/reporting/README.md) | Publish a run as reviewable evidence | `judgelab.report` |
| Application layer | Command line, configuration, wiring | `judgelab.cli`, `judgelab.config` |

## Components

| Component | Responsibility | Depends on |
|---|---|---|
| `cli` | Parse the command, wire the run, show progress and the summary, map failures to exit codes | everything below (composition root) |
| `config` | Load and validate the YAML config into an `EvaluationConfig` | `connectors.ConnectionProfile` |
| `connectors` | The `ModelConnector` port, its adapters, profiles, the registry, credential lookup, errors | provider SDKs (adapters only) |
| `benchmark` | Load and validate benchmarks into immutable `Benchmark` and `TestCase` values | — |
| `runner` | Run the target over a benchmark; judge every trustworthy answer; apply the stop rules | `connectors` (port only), `judge`, `scoring` |
| `judge` | Rubrics, the judge prompt, verdict parsing, `Judge.evaluate` | `connectors` (port only), `benchmark` |
| `scoring` | Outcomes, case results, the run summary | `judge`, `benchmark`, `connectors.ModelResponse` |
| `report` | Build the JSON report and write it | `scoring`, `benchmark`, `connectors` |

## Key flows

Each use case has its own analysis and design, with diagrams:

| Use case | Analysis | Design |
|---|---|---|
| UC-001 Configure model connections | [analysis](usecases/UC-001-configure-model-connections/analysis.md) | [design](usecases/UC-001-configure-model-connections/design.md) |
| UC-002 Prepare benchmark dataset | [analysis](usecases/UC-002-prepare-benchmark-dataset/analysis.md) | [design](usecases/UC-002-prepare-benchmark-dataset/design.md) |
| UC-003 Execute target model | [analysis](usecases/UC-003-execute-target-model/analysis.md) | [design](usecases/UC-003-execute-target-model/design.md) |
| UC-004 Evaluate responses | [analysis](usecases/UC-004-evaluate-responses/analysis.md) | [design](usecases/UC-004-evaluate-responses/design.md) |
| UC-005 Generate report | [analysis](usecases/UC-005-generate-report/analysis.md) | [design](usecases/UC-005-generate-report/design.md) |
| UC-006 Run complete evaluation | [analysis](usecases/UC-006-run-complete-evaluation/analysis.md) | [design](usecases/UC-006-run-complete-evaluation/design.md) |

## Design decisions

Recorded as ADRs in [decisions/](decisions/).

## DSA & patterns applied

| Concept | Where | Why |
|---|---|---|
| Adapter | `OpenAIConnector`, `AnthropicConnector` | Fit each SDK to the `ModelConnector` port |
| Strategy | `ModelConnector` implementations; `Rubric` as data | Swap provider or rubric without touching the core |
| Factory / Registry | `create_connector`, `CONNECTORS` (dict: provider → class) | Pick the adapter from configuration; O(1) lookup |
| Dependency Injection | `connector_factory` in `cli.main`; `Judge(connector, rubric)` | Tests inject fakes; the core creates nothing it depends on |
| Test Double (Fake) | `FakeConnector` | Deterministic tests with no network, key or cost |
| Observer (callbacks) | `on_target`, `on_result` in `runner` | Progress output without coupling the runner to the CLI |
| Anti-Corruption Layer | `translate_error` in each adapter | Provider exceptions never reach the core |
| Value Objects | frozen dataclasses throughout | Results can't change after they are recorded |
| Single pass, O(n) | `summarise` | Count outcomes in one pass over any iterable |
| Hash-based duplicate check | `load_benchmark` (`first_seen` dict) | Find duplicate case ids in O(n), naming the first occurrence |
