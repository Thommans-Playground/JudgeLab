# BenchmarkLoader

| Field | Value |
|---|---|
| Bounded Context | Benchmark |
| DDD Type | Domain Service |
| Aggregate | — |
| Ontology | `Benchmark` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `benchmark.load_benchmark` (+ `benchmark.BenchmarkError`) |
| Related | Builds: [Benchmark](benchmark.md), [TestCase](test-case.md) |

## Definition

The factory that reads a benchmark JSON file and builds a valid Benchmark aggregate, or raises one `BenchmarkError` that lists every problem it found.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `BENCHMARK_FIELDS` | `set[str]` | Value Object | yes | `{"id", "name", "cases"}`. |
| `CASE_FIELDS` | `set[str]` | Value Object | yes | `{"id", "question", "expected_answer"}`. |

`BenchmarkError(ValueError)` carries `path: Path` and `problems: list[str]`.

## Behaviours (commands)

- `load_benchmark(path: str | Path) -> Benchmark`: reads the file as UTF-8 JSON, checks fields and cases, and returns the aggregate. Raises `BenchmarkError`.

## Invariants

- A missing file, or invalid JSON with its line and column, is rejected with the reason (AC-002-02).
- A valid file loads with cases in file order (AC-002-01). The bundled sample loads (AC-002-03).
- Every problem is collected before raising, each with its location (AC-002-04, AC-002-08).
- Duplicate ids name the id and both positions (AC-002-05). Unknown fields are rejected (AC-002-06). An empty or missing `cases` list is rejected (AC-002-07).
- It never returns a partial benchmark.

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **Benchmark** (Benchmark): the aggregate this service builds.
- **`config.load_config`** (application layer): loads the YAML run config, which only names the dataset path.

## Design note (candidate)

Reading the file is edge I/O kept in a plain function in v0.1, by decision. If benchmarks come from a second source (a URL, a database, Moonshot datasets), split this into a `BenchmarkSource` port (reads raw data) and a pure validator (builds the aggregate).
