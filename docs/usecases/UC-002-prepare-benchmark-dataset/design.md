# UC-002 Design: Prepare benchmark dataset

> **Draft for review.** Design says *how* the code realises the [analysis](analysis.md): real classes, signatures, patterns and where they sit in the [hexagonal architecture](../../design.md). It describes the reference solution the codealongs build.

| Field | Value |
|---|---|
| Use case | [UC-002](README.md) |
| Slices | [T-002-01](T-002-01-json-dataset-loader.md) (JSON dataset loader), [T-002-02](T-002-02-test-case-validation.md) (test-case validation) |
| Code | `judgelab.benchmark`, called from `judgelab.cli` |
| Decisions | [ADR-001](../../decisions/ADR-001.md) (hexagonal), [ADR-002](../../decisions/ADR-002.md) (diagrams, as-built check) |

## 1. From analysis to design

| Analysis class | Design element | Hexagon role |
|---|---|---|
| Benchmark File Reader (boundary) | `Path.read_text(encoding="utf-8")` and `json.loads`, inside `load_benchmark` | Edge I/O, no port in v0.1 (by decision) |
| Prepare Benchmark (control) | `benchmark.load_benchmark(path)` with `_check_fields()` | Factory function at the edge of the core |
| Benchmark (entity, aggregate root) | `benchmark.Benchmark` | Core (Benchmark context) |
| Test Case (entity) | `benchmark.TestCase` | Core (Benchmark context) |
| Problem List (entity) | a local `problems: list[str]` | Transient, no class |
| Benchmark Error (entity) | `benchmark.BenchmarkError(path, problems)`, a `ValueError` | Core error type |

The file reader has no class and no port. In v0.1 there is one source of benchmarks, a JSON file, and tests use real files in `tmp_path`, so nothing needs to substitute it. [ADR-001](../../decisions/ADR-001.md)'s rule is to add a port when a second adapter or a test needs one.

The Problem List is a plain list of strings. Each problem is already a full sentence with its location; giving it a class would add a name without adding a rule.

## 2. Design classes

![UC-002 design classes](diagrams/design-classes.svg)

Source: [diagrams/design-classes.puml](diagrams/design-classes.puml)

## 3. Design sequences

**Main success scenario.** A valid file becomes a `Benchmark`:

![UC-002 design sequence](diagrams/design-sequence.svg)

Source: [diagrams/design-sequence.puml](diagrams/design-sequence.puml)

**Extensions 1a to 4d.** A file that can't be read stops at once with one problem. A file that parses is checked to the end, every problem goes into `problems`, and one `BenchmarkError` lists them all. The CLI prints it and exits 1:

![UC-002 design sequence, validation](diagrams/design-sequence-validation.svg)

Source: [diagrams/design-sequence-validation.puml](diagrams/design-sequence-validation.puml)

## 4. Patterns and principles

| Pattern / principle | Where | Why |
|---|---|---|
| Factory (aggregate factory) | `load_benchmark` is the only code that builds a `Benchmark` from outside data | Invariants are checked in one place, before the aggregate exists |
| Notification (collect, then raise) | `problems` list filled by `load_benchmark` and `_check_fields`, raised once as `BenchmarkError` | A file is fixed in one pass (AC-002-08) |
| Value objects / immutability | `Benchmark` and `TestCase` are frozen; `cases` is a `tuple` | A loaded benchmark can't be changed half-way through a run |
| Schema as data | `BENCHMARK_FIELDS`, `CASE_FIELDS` | Unknown and missing fields come from one set difference each (AC-002-06) |
| Fail fast at the edge | `cli.run_command` loads the benchmark before it creates any connector | No model is called for a bad file |
| Exception suppression of the cause | `raise BenchmarkError(...) from None` for file and JSON errors | The user sees one clear problem, not a Python traceback |

## 5. Rules from the analysis, and where the design keeps them

| Rule | Kept by |
|---|---|
| No model is called for a bad file | `cli.run_command` calls `load_benchmark` before `connector_factory`, and catches `BenchmarkError` (exit 1) |
| A Benchmark exists only if every invariant holds | `load_benchmark` returns `Benchmark(...)` only when `problems` is empty |
| Every problem, in one error | `_check_fields` appends instead of raising; the case loop `continue`s past a bad case |
| Read failures reported alone | `FileNotFoundError`, `JSONDecodeError` and a non-dict top level each raise at once with one problem |
| Problems give their location | `where` is `"benchmark"` or `f"cases[{index}]"`; `BenchmarkError` puts the path in its message |
| Unknown fields are errors | `set(obj) - fields` in `_check_fields` |
| Cases keep file order | cases are appended in `enumerate` order and frozen into a `tuple` |

## 6. Design notes and candidate refactorings

- **The aggregate does not guard itself.** `Benchmark` and `TestCase` are plain frozen dataclasses; the invariants live in `load_benchmark`. Code that builds a `Benchmark(...)` by hand (tests do) can break them. A `__post_init__` check, or a `Benchmark.create(...)` class method, would move the invariants onto the root, where DDD puts them. The cost is a second copy of the checks, or reshaping `_check_fields` to serve both.
- **A `BenchmarkSource` port.** `load_benchmark` mixes edge I/O (reading a file, parsing JSON) with domain checks. Splitting it into a `BenchmarkSource` port (returns raw records) and a validating factory would let other formats in without touching the rules: JSONL, CSV, or Project Moonshot's dataset format (`examples` with `input` and `target`). That is the second adapter ADR-001 waits for, so it is a v0.2 candidate.
- **Problems are strings.** A `Problem(location, message)` value object would let a report or an editor point at the field. Today the location is only inside the sentence.
- **Order within one case.** `_check_fields` reports unknown fields first, then missing or blank fields, each sorted by name. Across cases the order is file order, as the use case asks; inside one case it is "kind, then alphabetical", not the order the keys appear in the file.
- **Duplicates are checked only for usable cases.** A case with any field problem is skipped, so its id is neither checked nor remembered. A later duplicate of it isn't reported until the first one is fixed. That's a second pass, against the "one pass" goal, but only for a file that already has errors.
- **Read errors that aren't caught.** Only `FileNotFoundError` and `JSONDecodeError` become a `BenchmarkError`. A directory, a permission error or a file that isn't UTF-8 (`UnicodeDecodeError`) escapes as a Python exception, and the CLI shows a traceback. Catching `OSError` and `UnicodeDecodeError` would close the gap.
- **Unknown benchmark-level fields.** `_check_fields` also rejects unknown top-level keys ("benchmark has unknown field 'x'"). The use case lists only unknown case fields (4c); its business rule covers both, so the use case could say so.

## 7. Checking the design against the code (as-built)

Generate the as-built sequence from a test that exercises this design, and compare it with section 3:

```bash
uv run python .claude/skills/vbench-docs/scripts/asbuilt.py sequence \
  "tests/test_benchmark.py::test_loads_cases_in_order" -o docs/usecases/UC-002-prepare-benchmark-dataset/diagrams/as-built/sequence.puml
```

For the validation extension, trace `tests/test_benchmark.py::test_every_problem_is_reported_at_once`.

A difference is either design drift (update this page and say why) or a code bug (fix the code). See [ADR-002](../../decisions/ADR-002.md).
