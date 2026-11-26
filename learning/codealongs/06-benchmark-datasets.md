# Codealong 6: Benchmark Datasets

So far JudgeLab knows how to talk to models, but it has nothing to ask them. In this codealong you are going to give it its first set of questions. By the end you will have a JSON format for benchmarks, a sample benchmark with five general-knowledge questions, and a `load_benchmark()` function that turns a file into a `Benchmark` object, or, when the file is broken, tells you about *every* problem in it at once, each one with its exact location.

This sounds like the least exciting chapter of the series, and in a way it is: there is no model and no network anywhere in it. But a benchmark is the input to every evaluation you will ever run, and a typo in it is silent. If a case says `expected_anwser` instead of `expected_answer` and nothing complains, you will be grading models against an empty answer and wondering why they all fail. The loader is where those mistakes get caught.

> **AI-Assist level:** this is a guided codealong, so record this work as **AI-Assist L4**.

## 6.1 Before You Start

Make sure you are on an up-to-date `main` and create a topic branch for this work:

```bash
$ git switch main && git pull --ff-only
$ git switch -c feat/p1-benchmark-loader-T005
```

The work in this chapter covers two tasks from the v0.1 plan: [T005](../../docs/releases/v0.1/tasks/T005.md) (the JSON loader) and [T006](../../docs/releases/v0.1/tasks/T006.md) (validating the cases). Both live on this one branch, because a loader that doesn't validate is not really finished.

As always, I strongly recommend that you type the code yourself instead of copying and pasting it.

## 6.2 Writing the Acceptance Criteria First

Before writing any code, let's decide what "done" means. Open the task file for T005 and fill in its Objective and Acceptance criteria sections. Replace the empty `- [ ]` line with the three criteria below.

_docs/releases/v0.1/tasks/T005.md_: Objective and acceptance criteria

```markdown
## Objective

Load a benchmark of question and expected-answer cases from a JSON file.

## Acceptance criteria

- [ ] **T005-AC1**: A valid JSON benchmark loads into a `Benchmark` with its id, name and `TestCase`s in file order.
- [ ] **T005-AC2**: A missing file or invalid JSON raises a `BenchmarkError` naming the file and, for bad JSON, the line and column.
- [ ] **T005-AC3**: The bundled `benchmarks/sample.json` loads and has at least five cases.
```

Then do the same in the task file for T006:

_docs/releases/v0.1/tasks/T006.md_: Objective and acceptance criteria

```markdown
## Objective

Reject malformed benchmarks with errors that say exactly what to fix.

## Acceptance criteria

- [ ] **T006-AC1**: Required fields (benchmark `id`, `name`, `cases`; case `id`, `question`, `expected_answer`) must be non-empty strings, and errors give the location, like `cases[1].question`.
- [ ] **T006-AC2**: Duplicate case ids are rejected, naming the id and both positions.
- [ ] **T006-AC3**: Unknown fields are rejected, so typos like `expected_anwser` are caught.
- [ ] **T006-AC4**: An empty or missing case list is rejected.
- [ ] **T006-AC5**: Every problem in a file is reported at once, not one per run.
```

You know from earlier chapters that the test suite reads these files. Run `uv run pytest` now and you will see the eight new criteria in the acceptance table, all marked `not tested`. That is your to-do list for the rest of the chapter.

## 6.3 The Benchmark Format

A benchmark is a list of questions, each with the answer you expect. Here is the format I'm going to use, in the form of the sample benchmark that ships with JudgeLab. Create it in the `benchmarks` folder:

_benchmarks/sample.json_: The bundled sample benchmark

```json
{
  "id": "general-knowledge-v1",
  "name": "General knowledge (sample)",
  "cases": [
    {
      "id": "gk-001",
      "question": "What is the capital of France?",
      "expected_answer": "Paris"
    },
    {
      "id": "gk-002",
      "question": "What is the chemical symbol for gold?",
      "expected_answer": "Au"
    },
    {
      "id": "gk-003",
      "question": "Who wrote the novel Pride and Prejudice?",
      "expected_answer": "Jane Austen"
    },
    {
      "id": "gk-004",
      "question": "How many sides does a hexagon have?",
      "expected_answer": "Six"
    },
    {
      "id": "gk-005",
      "question": "Which planet in our solar system is the largest?",
      "expected_answer": "Jupiter"
    }
  ]
}
```

The benchmark has an `id`, which is meant for machines (it will end up in reports, and the `-v1` suffix leaves room for a `-v2` that changes the questions), and a `name`, which is meant for people. Then there is the list of `cases`. Each case has its own `id`, a `question` that will be sent to the model, and the `expected_answer` that the judge will compare the model's answer against.

The case ids matter more than they seem to. When a report says that case `gk-003` failed, you need to be able to find that exact case again, next week, after someone has added three new questions at the top of the file. That is why cases have ids instead of being identified by their position, and why, as you will see shortly, the loader refuses duplicate ids.

The `benchmarks` folder has an empty `.gitkeep` file in it. Its only job was to make Git track an otherwise empty folder, and now that the folder has a real file in it, you can delete it:

```bash
$ git rm benchmarks/.gitkeep
```

## 6.4 Test Cases and Benchmarks

Now let's write the Python side. Create a new module called `benchmark.py` in the `judgelab` package. I'm going to show you the complete file first, and then we'll go through it in three parts: the data types, the error, and the loader.

_src/judgelab/benchmark.py_: Benchmarks and the loader

```python
"""Benchmarks: named collections of test cases, loaded from JSON files."""

import json
from dataclasses import dataclass
from pathlib import Path

BENCHMARK_FIELDS = {"id", "name", "cases"}
CASE_FIELDS = {"id", "question", "expected_answer"}


@dataclass(frozen=True)
class TestCase:
    """One question and the answer we expect."""

    __test__ = False  # tell pytest this is not a test class, despite its name

    id: str
    question: str
    expected_answer: str


@dataclass(frozen=True)
class Benchmark:
    """A named collection of test cases, in file order."""

    id: str
    name: str
    cases: tuple[TestCase, ...]


class BenchmarkError(ValueError):
    """A benchmark file could not be loaded. `problems` lists every issue found."""

    def __init__(self, path: Path, problems: list[str]) -> None:
        self.path = path
        self.problems = problems
        details = "\n".join(f"  - {problem}" for problem in problems)
        super().__init__(f"invalid benchmark {path}:\n{details}")


def load_benchmark(path: str | Path) -> Benchmark:
    """Load and validate a benchmark file, reporting every problem at once."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BenchmarkError(path, ["file not found"]) from None
    except json.JSONDecodeError as e:
        raise BenchmarkError(
            path, [f"not valid JSON (line {e.lineno}, column {e.colno})"]
        ) from None

    problems: list[str] = []
    if not isinstance(data, dict):
        raise BenchmarkError(path, ["the top level must be an object with id, name and cases"])
    _check_fields(data, BENCHMARK_FIELDS, "benchmark", problems)

    raw_cases = data.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        problems.append("cases must be a non-empty list")
        raw_cases = []

    cases = []
    first_seen: dict[str, int] = {}  # case id -> index where it first appeared
    for index, raw in enumerate(raw_cases):
        where = f"cases[{index}]"
        if not isinstance(raw, dict):
            problems.append(f"{where} must be an object")
            continue
        if _check_fields(raw, CASE_FIELDS, where, problems):
            case = TestCase(raw["id"], raw["question"], raw["expected_answer"])
            if case.id in first_seen:
                problems.append(
                    f"{where}.id {case.id!r} duplicates cases[{first_seen[case.id]}].id"
                )
            else:
                first_seen[case.id] = index
            cases.append(case)

    if problems:
        raise BenchmarkError(path, problems)
    return Benchmark(id=data["id"], name=data["name"], cases=tuple(cases))


def _check_fields(obj: dict, fields: set[str], where: str, problems: list[str]) -> bool:
    """Check required string fields and unknown keys. Return True if obj is usable."""
    ok = True
    for key in sorted(set(obj) - fields):
        problems.append(f"{where} has unknown field {key!r}")
        ok = False
    for key in sorted(fields - {"cases"}):
        value = obj.get(key)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{where}.{key} must be a non-empty string")
            ok = False
    return ok
```

The two dataclasses at the top are the shapes that the rest of JudgeLab is going to work with. A `TestCase` is one question with its expected answer, and a `Benchmark` is a named collection of them. Like `ModelResponse`, both are frozen: a benchmark is part of the evidence of an evaluation, and once it is loaded, nothing should be able to change it.

Freezing the dataclass is not quite enough, though. A frozen dataclass stops you from assigning a new value to a field, but if the field holds a list, you could still call `benchmark.cases.append(...)` and change the list in place. That is why `Benchmark.cases` is a `tuple` and not a `list`. A tuple has no `append()`, no `remove()` and no item assignment, so a loaded benchmark can't be changed by accident, not even from the inside. The type hint `tuple[TestCase, ...]` means "a tuple of any length where every item is a `TestCase`".

### The `__test__` gotcha

You may be wondering about the strange `__test__ = False` line in `TestCase`. This one has a story behind it.

When pytest collects tests, it looks in every test module for functions whose names start with `test` and for classes whose names start with `Test`. It doesn't care where the class was defined. Your test module is going to do `from judgelab.benchmark import TestCase`, and as soon as it does, pytest sees a class called `TestCase` in that module and tries to collect it as a group of tests. It then discovers that the class has an `__init__()` method (the dataclass wrote one for you), gives up, and complains about it. I tried it by removing that line and running the tests, and this is what pytest printed (I've shortened the path):

```text
=============================== warnings summary ===============================
src/judgelab/benchmark.py:11
  .../src/judgelab/benchmark.py:11: PytestCollectionWarning: cannot collect test class 'TestCase' because it has a __init__ constructor (from: tests/test_benchmark.py)
    @dataclass(frozen=True)
```

The tests still pass, but a warning that shows up on every run is a warning that everybody learns to ignore, and then the next real one goes unnoticed. Pytest checks for a `__test__` attribute on anything it is about to collect, and when that attribute is `False`, it leaves the thing alone. So that one line tells pytest "despite my name, I'm not a test".

Couldn't I just call the class something else? I could, but "test case" is the standard name for this concept in the evaluation world, and it is the name used throughout the v0.1 plan. I'd rather keep the right name and add one line than invent a worse name to work around a tool.

Note that `__test__` has no type annotation. In a dataclass, only annotated class attributes become fields, so this one stays a plain class attribute and does not show up in the constructor or in the `repr`.

## 6.5 Reporting Every Problem at Once

The `BenchmarkError` class is the second part of the module. Think about how you fix a broken file when the tool tells you about one problem at a time: you run it, fix the first error, run it again, fix the second error, run it again... It's like a spell checker that stops at the first misspelled word. With a benchmark of a hundred cases, that gets old very quickly.

So instead of a single message, `BenchmarkError` carries a `problems` list with everything that is wrong with the file. Its message lists them all, one per line, under the name of the file. And because the list is kept as an attribute, code that wants to do something with the problems (the tests, for example) doesn't need to pick the message apart.

`BenchmarkError` inherits from `ValueError`, which is Python's standard exception for "the value you gave me has the right type but is not acceptable". That means a caller that knows nothing about JudgeLab can still catch it in a sensible way.

## 6.6 The Loader

The third part is `load_benchmark()`, and it works in two stages.

The first stage reads and parses the file. There are two ways this can go wrong, and both are fatal, since without valid JSON there is nothing else to check. A missing file raises `FileNotFoundError`, and invalid JSON raises `json.JSONDecodeError`, which conveniently has `lineno` and `colno` attributes that say exactly where the parser gave up. Both are converted into a `BenchmarkError` immediately. The `from None` at the end of these `raise` statements hides the original exception from the traceback. In chapter 1 you used `from e` to *keep* the cause, because the SDK's exception had useful details. Here the original exception adds nothing that our message doesn't already say, so showing it would just double the noise.

The same goes for a file whose top level is valid JSON, but not an object, like a list or a number. There is nothing useful to check in that case, so the loader stops right there.

The second stage is the validation, and here the loader changes strategy. Instead of raising at the first problem, it appends each problem to the `problems` list and keeps going. Only at the very end, if the list is not empty, does it raise a single `BenchmarkError` with all of them. This is what makes T006-AC5 possible.

Each problem names its location: `benchmark.name` for a field of the benchmark itself, and `cases[1].question` for a field of the second case (the index starts at zero, as in Python). The `where` variable builds this prefix for each case. When you open the file to fix it, you know exactly where to look.

The checks themselves are in the `_check_fields()` helper, which is used for both the benchmark object and each case. It does two things.

First, it rejects unknown fields. The expression `set(obj) - fields` is a set difference: all the keys in the object that are not in the list of allowed fields. This is the check that catches typos. Without it, a case with `expected_anwser` would be accepted with a missing answer, and the typo would only show up as a mysterious failure much later. Rejecting unknown fields is a choice, and it does mean that you can't add a `notes` field to a case without updating the loader. I'm happy with that trade-off: a format that changes on purpose is easy to deal with, a typo that is silently ignored is not.

Second, it checks that every required field is a string with something other than whitespace in it. Notice the `fields - {"cases"}` part. The benchmark's `cases` field is in `BENCHMARK_FIELDS` so that it counts as a known field, but it is a list, not a string, so it is checked separately in the loader.

The helper returns `True` if the object is usable, and the loader uses that answer to decide whether to build a `TestCase` from it. Both loops go through the keys in `sorted()` order, so the problems always come out in the same order. This is a small detail, but it makes the error messages predictable, and the tests depend on it.

### Finding duplicates in one pass

The last check is the one for duplicate case ids. The obvious way to find duplicates is to compare every case with every other case, with two nested loops. That works, but for `n` cases it makes about `n²/2` comparisons, which is what is called O(n²). For a benchmark of 10,000 cases, that is 50 million comparisons.

The loader does it in a single pass instead, with the help of a dictionary called `first_seen`, which maps each case id to the index where it first appeared. For each case, it asks the dictionary "have I seen this id before?". Looking up a key in a dictionary takes about the same time no matter how big the dictionary is, so the whole check is O(n): 10,000 cases, 10,000 lookups. And since the dictionary stores the index of the first occurrence, the error message can name both positions, as T006-AC2 asks.

If this sounds familiar, it is because this is the classic "Contains Duplicate" problem, which is the practice exercise listed for T005-T006 in the DSA and GoF learning ledger of the [v0.1 plan](../../docs/releases/v0.1/README.md). Solving it on its own, after this chapter, is a good way to make sure the idea sticks.

There is one more detail to notice: a case is only checked for duplicates if `_check_fields()` says it is valid. If a case is broken, its `id` might be missing, or not even a string, and comparing it with other ids would only produce confusing follow-up errors. The case has already been reported, so the loader moves on.

## 6.7 Trying It Out

Let's try the loader on the sample benchmark. Start a Python session with `uv run python` from the root of the project:

```python
>>> from judgelab.benchmark import load_benchmark
>>> b = load_benchmark("benchmarks/sample.json")
>>> b.name, len(b.cases), b.cases[0]
('General knowledge (sample)', 5, TestCase(id='gk-001', question='What is the capital of France?', expected_answer='Paris'))
```

Now let's see what happens with a file that has several problems in it. Create a file called `sandbox/broken.json` with these contents. Look closely, there are three mistakes in it:

_sandbox/broken.json_: A benchmark with mistakes

```json
{
  "id": "b1",
  "name": "",
  "cases": [
    {"id": "q1", "question": "2+2?", "expected_answer": "4"},
    {"id": "q2", "question": "3+3?", "expected_anwser": "6"},
    {"id": "q1", "question": "4+4?", "expected_answer": "8"}
  ]
}
```

And now try to load it:

```python
>>> load_benchmark("sandbox/broken.json")
judgelab.benchmark.BenchmarkError: invalid benchmark sandbox/broken.json:
  - benchmark.name must be a non-empty string
  - cases[1] has unknown field 'expected_anwser'
  - cases[1].expected_answer must be a non-empty string
  - cases[2].id 'q1' duplicates cases[0].id
```

All the problems are reported in one go. The empty name, the typo and the duplicate id are all there, and each one says exactly where it is.

You may have noticed that there are four problems listed for three mistakes. The typo produces two of them: `expected_anwser` is an unknown field, *and* because of the typo, the real `expected_answer` field is missing. Both statements are true, and together they point you straight at the fix.

Here is a question to think about: what would happen if the typo were in the *third* case instead of the second? Then the third case would not be valid, so it would never be checked for duplicates, and the `duplicates cases[0].id` line would disappear from the output. When you fix the typo and run the loader again, the duplicate would show up. This is the one situation where the loader takes two runs to show you everything, and it is the price of not producing confusing follow-up errors from broken cases.

You can also check that a loaded benchmark really can't be changed:

```python
>>> b.cases.append(1)
AttributeError: 'tuple' object has no attribute 'append'
>>> b.cases[0].id = "x"
FrozenInstanceError: cannot assign to field 'id'
```

The `sandbox/broken.json` file was only for this experiment, so you can delete it now.

## 6.8 The Tests

Now let's write the tests. Create a new test module:

_tests/test_benchmark.py_: Tests for the benchmark loader

```python
import json
from pathlib import Path

import pytest

from judgelab.benchmark import Benchmark, BenchmarkError, TestCase, load_benchmark

SAMPLE = Path(__file__).resolve().parents[1] / "benchmarks" / "sample.json"


def write(tmp_path, data):
    path = tmp_path / "bench.json"
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


def case(id_, question="Q?", answer="A"):
    return {"id": id_, "question": question, "expected_answer": answer}


def bench(*cases):
    return {"id": "b1", "name": "Bench", "cases": list(cases)}


def problems(path):
    with pytest.raises(BenchmarkError) as caught:
        load_benchmark(path)
    return caught.value.problems


@pytest.mark.acceptance("T005-AC1")
def test_loads_cases_in_order(tmp_path):
    path = write(
        tmp_path, bench(case("c1", "2+2?", "4"), case("c2", "Capital of France?", "Paris"))
    )
    assert load_benchmark(path) == Benchmark(
        id="b1",
        name="Bench",
        cases=(TestCase("c1", "2+2?", "4"), TestCase("c2", "Capital of France?", "Paris")),
    )


@pytest.mark.acceptance("T005-AC2")
def test_missing_file(tmp_path):
    with pytest.raises(BenchmarkError, match="nope.json") as caught:
        load_benchmark(tmp_path / "nope.json")
    assert caught.value.problems == ["file not found"]


@pytest.mark.acceptance("T005-AC2")
def test_invalid_json_gives_line_and_column(tmp_path):
    path = write(tmp_path, '{"id": "b1",\n  "name": }')
    assert problems(path) == ["not valid JSON (line 2, column 11)"]


@pytest.mark.acceptance("T005-AC3")
def test_sample_benchmark_loads():
    benchmark = load_benchmark(SAMPLE)
    assert benchmark.id == "general-knowledge-v1"
    assert len(benchmark.cases) >= 5


@pytest.mark.acceptance("T006-AC1")
def test_missing_and_blank_fields_give_their_location(tmp_path):
    path = write(tmp_path, bench(case("c1"), {"id": "c2", "question": " ", "expected_answer": "A"}))
    assert problems(path) == ["cases[1].question must be a non-empty string"]


@pytest.mark.acceptance("T006-AC1")
def test_benchmark_fields_are_required(tmp_path):
    path = write(tmp_path, {"cases": [case("c1")]})
    assert problems(path) == [
        "benchmark.id must be a non-empty string",
        "benchmark.name must be a non-empty string",
    ]


@pytest.mark.acceptance("T006-AC2")
def test_duplicate_ids_name_both_positions(tmp_path):
    path = write(tmp_path, bench(case("c1"), case("c2"), case("c1")))
    assert problems(path) == ["cases[2].id 'c1' duplicates cases[0].id"]


@pytest.mark.acceptance("T006-AC3")
def test_unknown_fields_are_rejected(tmp_path):
    typo = {"id": "c1", "question": "Q?", "expected_anwser": "A"}
    assert problems(write(tmp_path, bench(typo))) == [
        "cases[0] has unknown field 'expected_anwser'",
        "cases[0].expected_answer must be a non-empty string",
    ]


@pytest.mark.acceptance("T006-AC4")
@pytest.mark.parametrize("cases", [[], None])
def test_empty_or_missing_case_list(tmp_path, cases):
    data = {"id": "b1", "name": "Bench"} | ({} if cases is None else {"cases": cases})
    assert "cases must be a non-empty list" in problems(write(tmp_path, data))


@pytest.mark.acceptance("T006-AC5")
def test_every_problem_is_reported_at_once(tmp_path):
    path = write(tmp_path, {"id": "", "name": "Bench", "cases": [case("c1"), "oops", case("c1")]})
    assert problems(path) == [
        "benchmark.id must be a non-empty string",
        "cases[1] must be an object",
        "cases[2].id 'c1' duplicates cases[0].id",
    ]
```

These tests use a few techniques worth pointing out.

The `tmp_path` argument is a pytest fixture. Every test that asks for it gets a brand-new, empty temporary directory, which pytest cleans up for you later. The tests write their benchmark files there, so they never touch the real `benchmarks` folder and can't interfere with each other.

The four small helpers at the top keep the tests short enough to read at a glance. `write()` saves a benchmark to a file (either a dictionary, converted with `json.dumps()`, or a raw string, for the tests that need broken JSON). `case()` and `bench()` build valid data with sensible defaults, so each test only spells out the part that matters to it. And `problems()` loads a file that is expected to fail, and returns its list of problems. It uses `pytest.raises()` as a context manager with `as caught`, and after the block, `caught.value` is the exception that was raised.

Because `problems()` returns the whole list, most tests compare it with `==` against the exact list they expect. This checks more than it seems. It checks that every expected problem is there, that the messages are worded correctly, that they are in the right order, *and* that there are no extra problems. For example, `test_duplicate_ids_name_both_positions` would fail if the loader also reported the duplicate a second time.

The `test_invalid_json_gives_line_and_column` test writes a file where the error is on the second line, so that the test would catch a loader that always reported line 1. The `SAMPLE` path at the top is built from the test file's own location (`parents[1]` is the project root), so the test finds the sample benchmark no matter which directory you run pytest from. And `test_empty_or_missing_case_list` uses `parametrize` to run once with an empty list and once with no `cases` key at all. The `|` operator merges two dictionaries.

Finally, did you notice that `tests/test_benchmark.py` imports `TestCase`? That is exactly the import that would trigger the warning from section 6.4.

Let's run the whole test suite:

```bash
$ uv run pytest
```

The acceptance table at the end now has all of T005 and T006 in it. This is the relevant part, plus the last two lines:

```text
PASS        T005-AC1   A valid JSON benchmark loads into a `Benchmark` with its id, name and
PASS        T005-AC2   A missing file or invalid JSON raises a `BenchmarkError` naming the fi
PASS        T005-AC3   The bundled `benchmarks/sample.json` loads and has at least five cases
PASS        T006-AC1   Required fields (benchmark `id`, `name`, `cases`; case `id`, `question
PASS        T006-AC2   Duplicate case ids are rejected, naming the id and both positions.
PASS        T006-AC3   Unknown fields are rejected, so typos like `expected_anwser` are caugh
PASS        T006-AC4   An empty or missing case list is rejected.
PASS        T006-AC5   Every problem in a file is reported at once, not one per run.
...
37 PASS
104 passed in 2.28s
```

Your timing will be different, but every line should say `PASS`, and there should be no warnings.

## 6.9 Troubleshooting

- **`PytestCollectionWarning: cannot collect test class 'TestCase'`.** You forgot the `__test__ = False` line, or you gave it a type annotation (`__test__: bool = False`), which turns it into a dataclass field instead of a class attribute.
- **`test_sample_benchmark_loads` fails with `file not found`.** The sample file is not at `benchmarks/sample.json` in the project root. Check the folder name; it is plural.
- **The problems are right, but in a different order.** Check that both loops in `_check_fields()` use `sorted()`. Sets have no reliable order, so without it the order of the messages can change between runs.
- **`test_empty_or_missing_case_list[cases0]` fails, but `[None]` passes.** The empty list is getting through. Look at the `if` that checks `raw_cases`: it needs `not isinstance(raw_cases, list) or not raw_cases`. With `and` instead of `or`, a missing list is still caught, but an empty one is not.
- **`TypeError: unhashable type` when loading a file.** A case has a list or an object as its `id`, and the duplicate check tried to use it as a dictionary key. Make sure the duplicate check is inside the `if _check_fields(...)` block, so it only ever sees ids that passed the string check.

## 6.10 Exercises

1. Write a test for a file whose top level is a JSON list (`[]`) instead of an object. What does `problems()` return?
2. Without running it, predict the exact list of problems for a benchmark with one case, `{"id": 7, "question": "Q?", "expected_answer": "A", "notes": "x"}`. Then write a test and check your prediction.
3. Solve "Contains Duplicate" on its own: write a function that takes a list of integers and returns `True` if any value appears twice. Write it once with two nested loops and once with a set, and time both with a list of 20,000 distinct numbers.
4. Change `_check_fields()` so it also accepts an optional `notes` field on cases (a string), without weakening the typo check for everything else. Which tests would you add?

## 6.11 Committing Your Work

Once all the tests pass, you can mark the work as done. In both [T005](../../docs/releases/v0.1/tasks/T005.md) and [T006](../../docs/releases/v0.1/tasks/T006.md), tick the acceptance-criteria checkboxes (`- [ ]` becomes `- [x]`), set the Branch field to `feat/p1-benchmark-loader-T005`, Status to `Done` and AI-Assist to `L4`. Then check that the docs are still consistent:

```bash
$ python3 .claude/skills/vbench-docs/scripts/docids.py check
```

Now commit. Following [CONTRIBUTING.md](../../CONTRIBUTING.md), the commit message uses the Conventional Commits format, with a body that explains the design and an `AI-Assist` trailer:

```bash
$ git add benchmarks src/judgelab/benchmark.py tests/test_benchmark.py docs/releases/v0.1/tasks
$ git commit
```

```text
feat(benchmark): load and validate JSON benchmark files

Benchmarks are JSON files with an id, a name and a list of cases.
The loader collects every problem in a file and reports them all at
once, each with its location (like cases[1].question). Unknown fields
are rejected to catch typos, and duplicate case ids are found in one
pass with a dict of first positions (O(n), Contains Duplicate).

AI-Assist: L4
```

Finally, push the branch and open a pull request. The `vbench-pr` skill knows the PR conventions for this repository, so you can ask Claude Code to "open a PR" and review the title and body it proposes before it creates it. Once it is merged, delete the branch.

## 6.12 Wrapping Up

Congratulations, JudgeLab now has something to ask! You have a simple JSON format for benchmarks, a sample benchmark, and a loader that refuses to accept a broken file quietly. When it rejects a file it tells you everything that is wrong, with the location of each problem, so that you can fix it all in one go.

In the next chapter you are going to put the benchmark and the connectors together for the first time, and send each question to the model you are evaluating, the *target*. You will also have to decide what to do when one of those calls fails in the middle of a run.
