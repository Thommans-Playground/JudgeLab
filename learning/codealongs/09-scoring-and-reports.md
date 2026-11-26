# Codealong 9: Scoring and the JSON Report

In this codealong you are going to turn a pile of verdicts into an evaluation. By the end you will have an `evaluate()` function that sends every case to the target model and then to the judge, an `Outcome` for every case (`PASS`, `FAIL` or `ERROR`), a `Summary` with a pass rate that can never be quietly inflated or deflated by errors, and a JSON report on disk that a reviewer can read months from now to see exactly what happened.

Up to now, the pieces of JudgeLab have each done one job well: the connectors talk to models, `run_target()` collects the target's answers, and the `Judge` turns one answer into a validated verdict. Nothing yet connects them, and nothing keeps a record. That is what this chapter is about, and it is also where the most important promise in your v0.1 plan gets kept: errors are reported next to the pass rate, and never counted as failures.

> **AI-Assist level:** this is a guided codealong, so record your work as **L4**.

## 9.1 Before You Start

You need the code from chapter 8: the `judge.py` module with `Judge`, `JudgeEvaluation`, `JudgeError`, `build_judge_prompt()` and `get_rubric()`, and `run_target()` in `runner.py`. Run the tests to confirm that you are starting from a green suite:

```bash
$ uv run pytest -q
```

This chapter covers task T010 (aggregate calculations), T011 (the JSON report writer), and the first half of T012 (orchestration). Following [CONTRIBUTING.md](../../CONTRIBUTING.md), create a topic branch from an up-to-date `main`:

```bash
$ git switch main && git pull --ff-only && git switch -c feat/p1-scoring-report-T010
```

As always, I strongly recommend that you type the code yourself.

## 9.2 Writing the Acceptance Criteria First

Before writing any code, let's decide what "done" means. Open the three task files, [T010](../../docs/releases/v0.1/tasks/T010.md), [T011](../../docs/releases/v0.1/tasks/T011.md) and [T012](../../docs/releases/v0.1/tasks/T012.md), and add an objective and the acceptance criteria. In each one, replace the empty `- [ ]` line under "Acceptance criteria" with the lines below, and put the objective sentence under the "Objective" heading.

_docs/releases/v0.1/tasks/T010.md_: Objective and acceptance criteria

```markdown
## Objective

Summarise a run's outcomes transparently, never hiding errors.

## Acceptance criteria

- [ ] **T010-AC1**: Totals for passed, failed and errored cases are counted in a single pass over the results.
- [ ] **T010-AC2**: `pass_rate` is passed / (passed + failed): errors are never counted as failures, and the rate is `None` when nothing was evaluated.
- [ ] **T010-AC3**: `coverage` is the share of cases that reached a verdict, reported next to the pass rate.
```

_docs/releases/v0.1/tasks/T011.md_: Objective and acceptance criteria

```markdown
## Objective

Persist every case's evidence and the run's metadata as a reviewable JSON report.

## Acceptance criteria

- [ ] **T011-AC1**: Each case records its question, expected and actual answer, refusal, outcome, verdict and justification, both model calls (requested and served model, tokens, request id, latency) and any error with its stage.
- [ ] **T011-AC2**: The report records the run id, UTC start and finish times, JudgeLab version, benchmark, rubric, both connections (provider, model, base URL) and the summary.
- [ ] **T011-AC3**: The report never contains an API key or the name of the variable holding it.
- [ ] **T011-AC4**: Reports are written as UTF-8 JSON into an output directory (created if needed) with a unique, time-stamped file name.
```

_docs/releases/v0.1/tasks/T012.md_: Objective and acceptance criteria

```markdown
## Objective

Orchestrate a whole evaluation and expose it through a command line.

## Acceptance criteria

- [ ] **T012-AC1**: Every case goes to the target, then its answer goes to the judge; the judge's verdict becomes the case's PASS or FAIL outcome.
- [ ] **T012-AC2**: Target errors and truncated answers are ERROR at the target stage and are never sent to the judge.
- [ ] **T012-AC3**: Judge errors are ERROR at the judge stage, never FAIL; a judge auth or quota error stops judging the remaining cases.
- [ ] **T012-AC4**: A refusal from the target is sent to the judge as the answer, so the judge decides whether refusing was right.
```

T012 gets three more criteria in the next chapter, when the command line arrives. If you run `uv run pytest` now, the progress table at the bottom shows all eleven new criteria as `not tested`. Your job in this chapter is to turn them into `PASS`.

## 9.3 Three Outcomes

The judge only knows two words: `PASS` and `FAIL`. But a run has a third possibility, and it is the one that matters most for honest reporting: sometimes we simply don't know. The target timed out, or the judge replied with something that isn't JSON. Calling that a `FAIL` would blame the model for a problem with the plumbing, and dropping it silently would make the pass rate look better than the evidence supports. So the run needs its own vocabulary, with a separate word for "no verdict".

Create a new module for this vocabulary and for the summary of a run.

_src/judgelab/scoring.py_: Outcomes and the summary of a run

```python
"""Outcomes and the summary of a run."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from judgelab.benchmark import TestCase
from judgelab.connectors import ModelResponse
from judgelab.judge import JudgeEvaluation


class Outcome(StrEnum):
    PASS = "PASS"  # the judge says the answer is correct
    FAIL = "FAIL"  # the judge says the answer is wrong
    ERROR = "ERROR"  # we don't know: something failed before a verdict existed


@dataclass(frozen=True)
class CaseResult:
    """Everything that happened to one test case."""

    case: TestCase
    outcome: Outcome
    target: ModelResponse | None = None
    judgement: JudgeEvaluation | None = None
    error_stage: str | None = None  # "target" or "judge"
    error: str | None = None


@dataclass(frozen=True)
class Summary:
    total: int
    passed: int
    failed: int
    errors: int

    @property
    def evaluated(self) -> int:
        """Cases with a verdict. Errors are never counted as failures."""
        return self.passed + self.failed

    @property
    def pass_rate(self) -> float | None:
        """passed / (passed + failed), or None when nothing was evaluated."""
        return self.passed / self.evaluated if self.evaluated else None

    @property
    def coverage(self) -> float:
        """The share of cases that reached a verdict."""
        return self.evaluated / self.total if self.total else 0.0


def summarise(results: Iterable[CaseResult]) -> Summary:
    """Count outcomes in a single pass over the results."""
    counts = {outcome: 0 for outcome in Outcome}
    total = 0
    for result in results:
        counts[result.outcome] += 1
        total += 1
    return Summary(
        total=total,
        passed=counts[Outcome.PASS],
        failed=counts[Outcome.FAIL],
        errors=counts[Outcome.ERROR],
    )
```

Let's go through it one piece at a time.

`Outcome` is a `StrEnum`, the same kind of enum you used for `Verdict` in chapter 8. Its members are also real strings, so `Outcome.PASS == "PASS"` is true and an f-string prints `PASS` instead of `Outcome.PASS`. That will matter when the command line prints progress in the next chapter. You may wonder why I didn't just add `ERROR` to `Verdict`. The reason is that they belong to different parts of the system. `Verdict` is what the judge is allowed to say, and the judge must never be able to say `ERROR`. `Outcome` is what the *run* concluded about a case. Keeping them separate means a judge reply of `{"verdict": "ERROR"}` is still rejected by the parser, exactly as before.

`CaseResult` is the record of everything that happened to one case. Only `case` and `outcome` are required. The others default to `None` because not every case gets that far: a case whose target call failed has no target response and no judgement, only an `error` and the `error_stage` where it happened. The stage is there so a reviewer can tell at a glance whether the problem was the model under test or the judge.

`Summary` stores four numbers and *computes* the other three. This is the design choice I want you to notice most in this chapter. If `evaluated`, `pass_rate` and `coverage` were stored fields, someone could build a `Summary` where the pass rate disagrees with the counts, and nothing would catch it. As properties, they are derived from the counts every time you read them, so they can't disagree. There is one rule of thumb at work here: store facts, derive conclusions.

Look closely at the two divisions. `pass_rate` is `passed / evaluated`, where `evaluated` is `passed + failed`. Errors are not in the denominator, which is exactly what your [v0.1 plan](../../docs/releases/v0.1/README.md) asks for. And when nothing was evaluated, it returns `None` instead of dividing by zero. `None` means "there is no pass rate", which is the truth. Returning `0.0` would be a lie, because it would say the model failed everything when in fact we have no idea. `coverage`, on the other hand, returns `0.0` for an empty run, because "none of zero cases reached a verdict" really is zero coverage, and a reader needs to see the pass rate and the coverage side by side to judge how much to trust the rate.

Finally, `summarise()`. This is the "single-pass counting" entry from your DSA ledger (T010). The function walks over the results exactly once, keeping a running count per outcome in a dictionary that starts with a zero for every member of `Outcome`. That makes it O(n) in time and O(1) in extra space, since there are always three counters no matter how many results there are. It also means the function works on *any* iterable, including a one-shot generator, and that's not a minor detail, as you are about to see.

## 9.4 Trying the Scoring

Let's play with this in a Python session. Start one with `uv run python` from the root of the project:

```python
>>> from judgelab.benchmark import TestCase
>>> from judgelab.scoring import CaseResult, Outcome, summarise
>>> case = TestCase("c1", "2+2?", "4")
>>> outcomes = [Outcome.PASS, Outcome.FAIL, Outcome.PASS, Outcome.ERROR]
>>> summary = summarise(CaseResult(case, o) for o in outcomes)
>>> summary
Summary(total=4, passed=2, failed=1, errors=1)
>>> summary.evaluated, summary.pass_rate, summary.coverage
(3, 0.6666666666666666, 0.75)
>>> nothing = summarise([CaseResult(case, Outcome.ERROR)])
>>> nothing.pass_rate, nothing.coverage
(None, 0.0)
```

Notice that the pass rate is two out of three, not two out of four. The error is visible in `errors` and in the 75% coverage, but it does not drag the pass rate down.

Now, here is why the single pass matters. Suppose you had written `summarise()` the "obvious" way, with one `sum()` per outcome. Watch what happens with a generator:

```python
>>> results = (CaseResult(case, o) for o in outcomes)
>>> sum(1 for r in results if r.outcome == Outcome.PASS)
2
>>> sum(1 for r in results if r.outcome == Outcome.FAIL)
0
```

The first pass consumed the generator, so the second pass saw nothing and reported zero failures. There was no error and no warning, only a wrong number. Counting everything in one loop makes this bug impossible.

## 9.5 Evaluating a Benchmark

Now that there is a way to describe outcomes, let's produce them. The new `evaluate()` function works in two stages. The first stage is the `run_target()` function you wrote in chapter 7, unchanged. The second stage takes each of the target's results and decides its outcome, calling the judge when it makes sense to.

Open `src/judgelab/runner.py`. First, update the module docstring at the top to describe what the module now does:

_src/judgelab/runner.py_: New docstring

```python
"""Running a benchmark: ask the target model, then have the judge evaluate each answer."""
```

Then add two imports below the existing `from judgelab.connectors import (...)` block:

_src/judgelab/runner.py_: New imports

```python
from judgelab.judge import Judge, JudgeError
from judgelab.scoring import CaseResult, Outcome
```

Finally, add these two functions at the end of the file, below `run_target()`:

_src/judgelab/runner.py_: The `evaluate()` and `_judge()` functions

```python
def evaluate(
    benchmark: Benchmark,
    target: ModelConnector,
    judge: Judge,
    *,
    on_target: Callable[[TargetResult], None] | None = None,
    on_result: Callable[[CaseResult], None] | None = None,
) -> list[CaseResult]:
    """Run the target over the benchmark, then judge every answer we can trust."""
    results: list[CaseResult] = []
    judge_stopped_by: str | None = None

    for answered in run_target(benchmark, target, on_result=on_target):
        result, cause = _judge(answered, judge, judge_stopped_by)
        if judge_stopped_by is None and isinstance(cause, STOP_THE_RUN):
            judge_stopped_by = f"{type(cause).__name__} on case {answered.case.id}"
        results.append(result)
        if on_result:
            on_result(result)
    return results


def _judge(
    answered: TargetResult, judge: Judge, judge_stopped_by: str | None
) -> tuple[CaseResult, BaseException | None]:
    """Decide one case's outcome. Also returns the connector error behind a judge failure."""
    case, response = answered.case, answered.response
    if answered.error is not None:
        error = f"{type(answered.error).__name__}: {answered.error}"
        return CaseResult(case, Outcome.ERROR, error_stage="target", error=error), None
    if response.truncated:
        error = "answer was cut off by its length limit"
        return CaseResult(case, Outcome.ERROR, response, error_stage="target", error=error), None
    if judge_stopped_by:
        error = f"not judged: judging stopped after {judge_stopped_by}"
        return CaseResult(case, Outcome.ERROR, response, error_stage="judge", error=error), None

    # A refusal is still an answer: the judge decides whether refusing was right.
    actual = response.text if response.text is not None else f"[refused] {response.refusal}"
    try:
        judgement = judge.evaluate(case, actual)
    except JudgeError as e:
        failed = CaseResult(case, Outcome.ERROR, response, error_stage="judge", error=str(e))
        return failed, e.__cause__
    return CaseResult(case, Outcome(judgement.verdict), response, judgement), None
```

Let's start with `evaluate()`, which is the orchestrator. Because `run_target()` returns a complete list, all the target calls happen first, and only then does the loop start judging. That is the two-stage design: the target's answers are collected without any interference from the judge, and the judge works on a finished set of answers. The function reuses `run_target()` instead of rewriting its loop, so everything you built in chapter 7 still applies: a target auth or quota error still stops the target stage, and the cases that were never sent come back as errors. The two optional callbacks report progress from each stage, and the command line will use one of them in the next chapter.

The interesting decisions are all in `_judge()`, which looks at one target result and returns its `CaseResult`. It checks the possibilities in order:

1. **The target call failed.** The outcome is `ERROR` at the `"target"` stage, and the message includes the error's class name, so `ConnectorUnavailableError: HTTP 503` tells you both what kind of failure it was and the detail. The judge is never called, because there is nothing to judge.
2. **The answer was truncated.** The `truncated` flag from chapter 4 says that the model hit its length limit and stopped mid-answer. This is also an `ERROR` at the target stage, and it is never judged. Why not let the judge look at it? Because judging half an answer is unfair in both directions. If the judge says `FAIL`, it is penalising the model for a limit *we* set. If it says `PASS`, it is approving an answer it never saw the end of. The honest outcome is "we don't know", and the fix is to raise the limit and run again.
3. **Judging has been stopped.** More on this in a moment.
4. **Otherwise, call the judge.** If the judge succeeds, its `Verdict` becomes the case's `Outcome`. The expression `Outcome(judgement.verdict)` works because both enums are string-valued: `Verdict.FAIL` has the value `"FAIL"`, and `Outcome("FAIL")` looks that up. If the judge fails, which in chapter 8 always means a `JudgeError`, the outcome is `ERROR` at the `"judge"` stage. A broken judge reply never becomes a `FAIL`.

Notice how refusals are handled. A model that refuses has `text=None` and a `refusal` message. Instead of treating that as an error, `_judge()` sends the judge the refusal itself, prefixed with `[refused]`, as the actual answer. Then the judge decides. For a general-knowledge question, refusing to name the capital of France is wrong, and the `semantic_correctness` rubric says so explicitly. For a safety benchmark, a refusal may be exactly the right answer. Which one it is depends on the rubric, so the decision belongs to the judge, not to the runner.

Now for the stopping logic. In chapter 7, an auth or quota error from the target stopped the run, because the same error would repeat on every remaining call. The same is true for the judge: if the judge's API key is wrong, there is no point sending it four more requests. But `_judge()` only ever sees a `JudgeError`, not the connector error behind it. How can it tell an auth failure from a malformed reply?

This is where a small decision from chapter 8 pays off. The judge raised its error with `raise JudgeError(...) from e`, which stores the original connector error in the `__cause__` attribute of the `JudgeError`. A malformed or refused reply was raised without a connector error behind it, so its `__cause__` is `None`. That means `_judge()` can return `e.__cause__` alongside the result, and `evaluate()` checks it against the same `STOP_THE_RUN` tuple that `run_target()` uses. The first time the cause is an auth or quota error, `judge_stopped_by` records which error and which case, and every later case comes back as `ERROR` at the judge stage with a message saying why it was not judged. Their target answers are still kept in the result, so no evidence is lost.

You may wonder why `_judge()` returns a tuple instead of updating some state itself. Keeping it a function that receives everything it needs and returns everything it decides makes it easy to read in isolation, and the only piece of state, `judge_stopped_by`, lives in one place: the loop that owns it.

## 9.6 Seeing an Evaluation

Let's watch `evaluate()` work, using `FakeConnector`s so nothing leaves your computer. This uses the sample benchmark from chapter 6, so start `uv run python` from the root of the project:

```python
>>> from judgelab.benchmark import load_benchmark
>>> from judgelab.connectors import ConnectorUnavailableError, FakeConnector, Refusal
>>> from judgelab.judge import Judge, build_judge_prompt, get_rubric
>>> from judgelab.runner import evaluate
>>> from judgelab.scoring import summarise
>>> b = load_benchmark("benchmarks/sample.json")
>>> france, gold, novel, hexagon, planet = b.cases
>>> target = FakeConnector(model="target-model", replies={
...     france.question: "Paris",
...     gold.question: ConnectorUnavailableError("HTTP 503"),
...     novel.question: Refusal("I'd rather not say."),
...     hexagon.question: "6",
...     planet.question: "Jupiter",
... })
>>> PASS = '{"verdict": "PASS", "justification": "Correct."}'
>>> FAIL = '{"verdict": "FAIL", "justification": "The model refused to answer."}'
>>> refused = build_judge_prompt(novel, "[refused] I'd rather not say.")
>>> judge = Judge(FakeConnector(model="judge-model", default=PASS, replies={refused: FAIL}),
...               get_rubric("semantic_correctness"))
>>> results = evaluate(b, target, judge)
>>> for r in results:
...     print(r.case.id, r.outcome, r.error_stage, r.error)
...
gk-001 PASS None None
gk-002 ERROR target ConnectorUnavailableError: HTTP 503
gk-003 FAIL None None
gk-004 PASS None None
gk-005 PASS None None
>>> len(judge.connector.prompts)
4
>>> summary = summarise(results)
>>> summary
Summary(total=5, passed=3, failed=1, errors=1)
>>> summary.evaluated, summary.pass_rate, summary.coverage
(4, 0.75, 0.8)
```

The fake judge was scripted to fail the refusal and pass everything else. There are a few things to see here. The failed target call became an `ERROR` at the target stage. The refusal reached the judge (its scripted reply only matches a prompt containing `[refused] I'd rather not say.`) and came back as a `FAIL`. The judge received four prompts, not five, because `gk-002` never got that far. And the pass rate is three out of four evaluated, with the error showing up as 80% coverage instead of as a failure.

Keep this session open, because you are going to use these results in a moment.

## 9.7 The JSON Report

An evaluation that only exists in memory is gone when the process ends. Your plan asks for a report that records every case's evidence plus enough about the run to reproduce and trust it (REQ-010), and that never contains a secret (REQ-013). Let's write it.

_src/judgelab/report.py_: The JSON report

```python
"""The JSON report: per-case evidence plus the run's metadata and summary."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from judgelab.benchmark import Benchmark
from judgelab.connectors import ModelConnector, ModelResponse
from judgelab.scoring import CaseResult, Summary

REPORT_VERSION = "1"


@dataclass(frozen=True)
class RunInfo:
    """What was run, with what, and when."""

    benchmark: Benchmark
    rubric_id: str
    target: ModelConnector
    judge: ModelConnector
    started_at: datetime
    finished_at: datetime
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)


def build_report(run: RunInfo, results: list[CaseResult], summary: Summary) -> dict:
    """Everything a reviewer needs, as plain data. Never includes secrets."""
    return {
        "report_version": REPORT_VERSION,
        "run": {
            "id": run.run_id,
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat(),
            "judgelab_version": version("judgelab"),
        },
        "benchmark": {
            "id": run.benchmark.id,
            "name": run.benchmark.name,
            "cases": len(run.benchmark.cases),
        },
        "rubric": run.rubric_id,
        "connections": {"target": _connection(run.target), "judge": _connection(run.judge)},
        "summary": {
            "total": summary.total,
            "passed": summary.passed,
            "failed": summary.failed,
            "errors": summary.errors,
            "evaluated": summary.evaluated,
            "pass_rate": summary.pass_rate,
            "coverage": summary.coverage,
        },
        "cases": [_case(result) for result in results],
    }


def write_report(report: dict, directory: str | Path) -> Path:
    """Write the report as UTF-8 JSON into `directory`, creating it if needed."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    started = datetime.fromisoformat(report["run"]["started_at"])
    path = directory / f"run-{started:%Y%m%dT%H%M%SZ}-{report['run']['id'][:8]}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def utc_now() -> datetime:
    return datetime.now(UTC)


def _connection(connector: ModelConnector) -> dict:
    return {
        "provider": connector.provider,
        "model": connector.model,
        "base_url": connector.base_url,
    }


def _call(response: ModelResponse) -> dict:
    return {
        "requested_model": response.requested_model,
        "served_model": response.served_model,
        "finish_reason": response.finish_reason,
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "request_id": response.request_id,
        "latency_ms": round(response.latency_ms, 1),
    }


def _case(result: CaseResult) -> dict:
    target, judgement = result.target, result.judgement
    return {
        "id": result.case.id,
        "question": result.case.question,
        "expected_answer": result.case.expected_answer,
        "outcome": result.outcome.value,
        "actual_answer": target.text if target else None,
        "refusal": target.refusal if target else None,
        "verdict": judgement.verdict.value if judgement else None,
        "justification": judgement.justification if judgement else None,
        "target_call": _call(target) if target else None,
        "judge_call": _call(judgement.response) if judgement else None,
        "error": {"stage": result.error_stage, "message": result.error} if result.error else None,
    }
```

This module is split in two on purpose. `build_report()` turns the run into plain data, which means dictionaries, lists, strings, numbers and `None`, and `write_report()` puts that data on disk. Building the report doesn't touch the file system, so the tests can check its contents directly, and writing it doesn't know anything about evaluations.

`RunInfo` collects the facts about the run that aren't in the results: what was evaluated, with which rubric and connectors, and when. Look at how `run_id` gets its default. If I had written `run_id: str = uuid.uuid4().hex`, Python would have called `uuid4()` once, when the class was defined, and every run would get the same id. This is the same trap as the default argument that stored your API key in chapter 1. `field(default_factory=...)` tells the dataclass to call the function each time an instance is created instead.

`utc_now()` is a one-liner, but it's worth having. `datetime.now()` without an argument returns a "naive" datetime with no time zone attached, and when you read it back later you can't tell whether it was London time or Singapore time. `datetime.now(UTC)` returns an aware datetime, and its `isoformat()` ends in `+00:00`, so the report says exactly which moment it means. Everything in JudgeLab that records a time should call this function.

`judgelab_version` comes from `importlib.metadata.version("judgelab")`. That reads the version of the installed package, which `uv` took from the `version` field in your `pyproject.toml`. There's only one place where the version is written down, so the report and the package can't disagree. The `report_version` field is different: it versions the *shape* of the report, so that a script reading old reports in a year's time can tell which layout it is looking at.

Then there's `_connection()`, which is where REQ-013 is enforced. A connector is described by its provider, model and base URL, and nothing else. In particular, the `api_key_env` setting from the connection profile is not there, even though it is only a name. A report is evidence that you might attach to a review or share with someone outside your team, and the simplest way to be sure it says nothing about credentials is to never put credential information in it at all. The test you'll write in a moment proves this by building a report with a real `OpenAIConnector` and searching the written file for both the key and the variable name.

`_case()` flattens a `CaseResult` into the evidence for one case. Every key is always present, with `None` when a stage never happened. A reviewer, or a script, can then read `case["verdict"]` without first checking whether the key exists. Both model calls are recorded with `_call()`, including the served model and the request id, so if a verdict looks strange you can trace it back to the exact request on the provider's side. The latency is rounded to one decimal place, because sub-microsecond digits are noise.

Now look at `write_report()`. The `mkdir(parents=True, exist_ok=True)` call creates the directory and any missing parents, and does nothing if it already exists, so the caller never has to prepare the folder. The file name is built from the run's start time and the first eight characters of its id, like `run-20261127T093000Z-3f9c2a1b.json`. Starting with the timestamp means the files sort in chronological order in any file listing, and the id fragment means two runs that start in the same second still get different names, so one report never overwrites another. The `Z` in the name is a literal character, meaning "UTC", and it's only true because `started_at` comes from `utc_now()`.

Finally, the JSON itself is written with `indent=2` so that a human can read it, and with `ensure_ascii=False` so that a name like "Brontë" is stored as it is instead of as `ë`. Since the file can now contain non-ASCII characters, the encoding is given explicitly as UTF-8. Without it, Python would use your operating system's default encoding, which isn't UTF-8 on every machine.

## 9.8 Writing a Report

Back in the Python session from section 9.6, let's turn those results into a report:

```python
>>> from judgelab.report import RunInfo, build_report, utc_now, write_report
>>> now = utc_now()
>>> run = RunInfo(b, "semantic_correctness", target, judge.connector, now, now)
>>> report = build_report(run, results, summary)
>>> report["summary"]
{'total': 5, 'passed': 3, 'failed': 1, 'errors': 1, 'evaluated': 4, 'pass_rate': 0.75, 'coverage': 0.8}
>>> report["cases"][1]["error"]
{'stage': 'target', 'message': 'ConnectorUnavailableError: HTTP 503'}
>>> path = write_report(report, "reports")
>>> path.name
'run-20261126T171531Z-9504b63a.json'
```

Your file name will have a different time and id, of course. Open the file in your editor. The top of it describes the run:

```json
{
  "report_version": "1",
  "run": {
    "id": "9504b63aab3c4e168b632e025ae0f1b5",
    "started_at": "2026-11-26T17:15:31.700684+00:00",
    "finished_at": "2026-11-26T17:15:31.700684+00:00",
    "judgelab_version": "0.1.0"
  },
  "benchmark": {
    "id": "general-knowledge-v1",
    "name": "General knowledge (sample)",
    "cases": 5
  },
  "rubric": "semantic_correctness",
  "connections": {
    "target": {
      "provider": "fake",
      "model": "target-model",
      "base_url": null
    },
    "judge": {
      "provider": "fake",
      "model": "judge-model",
      "base_url": null
    }
  },
  "summary": {
    "total": 5,
    "passed": 3,
    "failed": 1,
    "errors": 1,
    "evaluated": 4,
    "pass_rate": 0.75,
    "coverage": 0.8
  },
  "cases": [
```

And further down, the `cases` list has one entry per case. Here are the error and the refusal:

```json
    {
      "id": "gk-002",
      "question": "What is the chemical symbol for gold?",
      "expected_answer": "Au",
      "outcome": "ERROR",
      "actual_answer": null,
      "refusal": null,
      "verdict": null,
      "justification": null,
      "target_call": null,
      "judge_call": null,
      "error": {
        "stage": "target",
        "message": "ConnectorUnavailableError: HTTP 503"
      }
    },
    {
      "id": "gk-003",
      "question": "Who wrote the novel Pride and Prejudice?",
      "expected_answer": "Jane Austen",
      "outcome": "FAIL",
      "actual_answer": null,
      "refusal": "I'd rather not say.",
      "verdict": "FAIL",
      "justification": "The model refused to answer.",
      "target_call": {
        "requested_model": "target-model",
        "served_model": "target-model",
        "finish_reason": "refusal",
        "prompt_tokens": 7,
        "completion_tokens": 0,
        "request_id": "fake-3",
        "latency_ms": 0.0
      },
      "judge_call": {
        "requested_model": "judge-model",
        "served_model": "judge-model",
        "finish_reason": "stop",
        "prompt_tokens": 20,
        "completion_tokens": 8,
        "request_id": "fake-2",
        "latency_ms": 0.0
      },
      "error": null
    },
```

Imagine you are a reviewer who wasn't there when this ran. Can you tell what happened to `gk-003`? The target refused, the judge was shown the refusal and failed it, and you have the request ids of both calls if you need to dig deeper. That is what "reviewable" means. The fake request ids look odd (`fake-3` for the target and `fake-2` for the judge) because each `FakeConnector` simply numbers its own calls, and the judge never saw `gk-002`.

When you are done exploring, delete the folder with `rm -r reports`. In the next chapter you are going to tell Git to ignore it, but for now you don't want it showing up in `git status`.

## 9.9 Tests

Time to prove all of this with tests. There are three new test files, one per module.

_tests/test_scoring.py_: Tests for outcomes and the summary

```python
import pytest

from judgelab.benchmark import TestCase
from judgelab.scoring import CaseResult, Outcome, Summary, summarise

CASE = TestCase("c", "Q?", "A")


def results(*outcomes):
    return [CaseResult(CASE, outcome) for outcome in outcomes]


@pytest.mark.acceptance("T010-AC1")
def test_counts_each_outcome():
    summary = summarise(results(Outcome.PASS, Outcome.FAIL, Outcome.PASS, Outcome.ERROR))
    assert summary == Summary(total=4, passed=2, failed=1, errors=1)


@pytest.mark.acceptance("T010-AC1")
def test_summarise_works_on_a_single_pass_iterator():
    summary = summarise(iter(results(Outcome.PASS, Outcome.ERROR)))
    assert (summary.total, summary.passed, summary.errors) == (2, 1, 1)


@pytest.mark.acceptance("T010-AC2")
def test_pass_rate_excludes_errors():
    summary = summarise(results(Outcome.PASS, Outcome.FAIL, Outcome.ERROR, Outcome.ERROR))
    assert summary.evaluated == 2
    assert summary.pass_rate == 0.5  # 1 / (1 + 1), not 1 / 4


@pytest.mark.acceptance("T010-AC2")
def test_pass_rate_is_none_when_nothing_was_evaluated():
    assert summarise(results(Outcome.ERROR, Outcome.ERROR)).pass_rate is None
    assert summarise([]).pass_rate is None


@pytest.mark.acceptance("T010-AC3")
def test_coverage_is_the_share_with_a_verdict():
    summary = summarise(results(Outcome.PASS, Outcome.FAIL, Outcome.FAIL, Outcome.ERROR))
    assert summary.coverage == 0.75
    assert summarise([]).coverage == 0.0
```

These are straightforward, but two of them deserve a comment. `test_summarise_works_on_a_single_pass_iterator` wraps the list in `iter()`, which turns it into an iterator that can only be read once, the same situation you saw in section 9.4. If someone "simplifies" `summarise()` into several passes later, this test fails. And `test_counts_each_outcome` compares against a whole `Summary` with `==`. Dataclasses compare field by field, and since the derived values are properties and not fields, the comparison checks just the four counts.

_tests/test_evaluate.py_: Tests for the orchestration

```python
from dataclasses import replace

import pytest

from judgelab.benchmark import Benchmark, TestCase
from judgelab.connectors import (
    ConnectorAuthError,
    ConnectorUnavailableError,
    FakeConnector,
    Refusal,
)
from judgelab.judge import SEMANTIC_CORRECTNESS, Judge, build_judge_prompt
from judgelab.runner import evaluate
from judgelab.scoring import Outcome

C1 = TestCase("c1", "Capital of France?", "Paris")
C2 = TestCase("c2", "2+2?", "4")
C3 = TestCase("c3", "Largest planet?", "Jupiter")
BENCH = Benchmark("b1", "Bench", (C1, C2, C3))

PASS = '{"verdict": "PASS", "justification": "Correct."}'
FAIL = '{"verdict": "FAIL", "justification": "Wrong."}'


def judge_with(replies, default=PASS):
    return Judge(
        FakeConnector(model="judge", replies=replies, default=default), SEMANTIC_CORRECTNESS
    )


def outcomes(results):
    return [(r.case.id, r.outcome, r.error_stage) for r in results]


@pytest.mark.acceptance("T012-AC1")
def test_each_answer_is_judged_and_the_verdict_is_the_outcome():
    target = FakeConnector(replies={C1.question: "Paris", C2.question: "5", C3.question: "Jupiter"})
    judge = judge_with({build_judge_prompt(C2, "5"): FAIL})
    results = evaluate(BENCH, target, judge)
    assert outcomes(results) == [
        ("c1", Outcome.PASS, None),
        ("c2", Outcome.FAIL, None),
        ("c3", Outcome.PASS, None),
    ]
    assert results[1].judgement.justification == "Wrong."
    assert results[0].target.text == "Paris"


@pytest.mark.acceptance("T012-AC2")
def test_target_errors_and_truncated_answers_are_errors_and_not_judged():
    class TruncatesC3(FakeConnector):
        def generate(self, prompt, *, instructions=None):
            response = super().generate(prompt, instructions=instructions)
            return replace(response, truncated=prompt == C3.question)

    target = TruncatesC3(
        replies={
            C1.question: "Paris",
            C2.question: ConnectorUnavailableError("HTTP 500"),
            C3.question: "Jup",
        }
    )
    judge = judge_with({})
    results = evaluate(BENCH, target, judge)
    assert outcomes(results) == [
        ("c1", Outcome.PASS, None),
        ("c2", Outcome.ERROR, "target"),
        ("c3", Outcome.ERROR, "target"),
    ]
    assert results[1].error == "ConnectorUnavailableError: HTTP 500"
    assert results[2].error == "answer was cut off by its length limit"
    assert len(judge.connector.prompts) == 1  # only c1 reached the judge


@pytest.mark.acceptance("T012-AC3")
def test_judge_errors_are_errors_not_failures():
    target = FakeConnector(default="Paris")
    judge = judge_with({build_judge_prompt(C2, "Paris"): "I think it's fine"})
    results = evaluate(BENCH, target, judge)
    assert outcomes(results)[1] == ("c2", Outcome.ERROR, "judge")
    assert results[1].error == "judge reply is not valid JSON"


@pytest.mark.acceptance("T012-AC3")
def test_judge_auth_error_stops_judging():
    target = FakeConnector(default="Paris")
    judge = judge_with({build_judge_prompt(C2, "Paris"): ConnectorAuthError("HTTP 401")})
    results = evaluate(BENCH, target, judge)
    assert outcomes(results) == [
        ("c1", Outcome.PASS, None),
        ("c2", Outcome.ERROR, "judge"),
        ("c3", Outcome.ERROR, "judge"),
    ]
    assert results[2].error == "not judged: judging stopped after ConnectorAuthError on case c2"
    assert len(judge.connector.prompts) == 2


@pytest.mark.acceptance("T012-AC4")
def test_refusals_are_sent_to_the_judge():
    target = FakeConnector(replies={C1.question: Refusal("I can't share that.")}, default="ok")
    judge = judge_with({})
    evaluate(Benchmark("b", "B", (C1,)), target, judge)
    assert judge.connector.prompts == [build_judge_prompt(C1, "[refused] I can't share that.")]


@pytest.mark.acceptance("T012-AC1")
def test_progress_callbacks_see_both_stages():
    seen = []
    evaluate(
        BENCH,
        FakeConnector(default="x"),
        judge_with({}),
        on_target=lambda r: seen.append(("target", r.case.id)),
        on_result=lambda r: seen.append(("result", r.case.id)),
    )
    assert seen.count(("target", "c1")) == 1 and seen.count(("result", "c3")) == 1
```

Here are the techniques worth learning from this file.

**Scripting the judge by prompt.** The fake judge's `replies` are keyed by the exact prompt it will receive, and `build_judge_prompt()` produces that key. So `judge_with({build_judge_prompt(C2, "5"): FAIL})` reads as "when the judge is asked about C2 with the answer 5, it says FAIL", and every other prompt gets the default `PASS`. The test uses the real prompt builder instead of a hand-typed string, so it stays correct if the prompt format ever changes.

**Asserting what *didn't* happen.** Your `FakeConnector` records every prompt it receives. `len(judge.connector.prompts) == 1` is how the AC2 test proves that the failed and truncated cases were never sent to the judge, and `== 2` is how the AC3 test proves that judging really stopped after the auth error instead of carrying on. A test that only checked outcomes couldn't tell "stopped" apart from "tried and failed every time".

**A one-off subclass for one odd behaviour.** `FakeConnector` has no way to script a truncated answer, and it doesn't need one, because this is the only test that wants it. `TruncatesC3` is a tiny subclass defined inside the test that calls the real `generate()` and then uses `dataclasses.replace()` to return a copy of the frozen response with `truncated` set to `True` for C3 only. `replace()` is the standard way to "change" a frozen dataclass: you don't modify it, you make a new one with one field different.

**Comparing tuples.** The `outcomes()` helper reduces each result to `(id, outcome, stage)`, so one `assert` checks the whole run, and if it fails, pytest shows you the full list side by side with the expected one.

_tests/test_report.py_: Tests for the report

```python
import json
from datetime import UTC, datetime

import pytest

from judgelab.benchmark import Benchmark, TestCase
from judgelab.connectors import ConnectorUnavailableError, FakeConnector, OpenAIConnector
from judgelab.judge import SEMANTIC_CORRECTNESS, Judge
from judgelab.report import RunInfo, build_report, write_report
from judgelab.runner import evaluate
from judgelab.scoring import summarise

BENCH = Benchmark(
    "b1",
    "Bench",
    (TestCase("c1", "Capital of France?", "Paris"), TestCase("c2", "2+2?", "4")),
)
SECRET = "sk-report-SECRET-9999"
START = datetime(2026, 11, 27, 9, 30, 0, tzinfo=UTC)
END = datetime(2026, 11, 27, 9, 30, 4, tzinfo=UTC)


@pytest.fixture
def report(monkeypatch):
    monkeypatch.setenv("REPORT_TEST_KEY", SECRET)
    target = FakeConnector(
        model="target-model",
        replies={"Capital of France?": "Paris", "2+2?": ConnectorUnavailableError("HTTP 503")},
    )
    judge_connector = FakeConnector(
        model="judge-model", default='{"verdict": "PASS", "justification": "Correct."}'
    )
    results = evaluate(BENCH, target, Judge(judge_connector, SEMANTIC_CORRECTNESS))
    # A real connector (holding the key) is also described, to prove no secret leaks.
    real_judge = OpenAIConnector(model="gpt-judge", api_key_env="REPORT_TEST_KEY")
    run = RunInfo(
        BENCH, "semantic_correctness", target, real_judge, START, END, run_id="abc123ef99"
    )
    return build_report(run, results, summarise(results))


@pytest.mark.acceptance("T011-AC1")
def test_cases_carry_their_evidence(report):
    passed, errored = report["cases"]
    assert passed["id"] == "c1" and passed["outcome"] == "PASS"
    assert (passed["question"], passed["expected_answer"], passed["actual_answer"]) == (
        "Capital of France?",
        "Paris",
        "Paris",
    )
    assert (passed["verdict"], passed["justification"]) == ("PASS", "Correct.")
    assert passed["target_call"]["served_model"] == "target-model"
    assert passed["judge_call"]["served_model"] == "judge-model"
    assert passed["error"] is None
    assert errored["outcome"] == "ERROR"
    assert errored["error"] == {
        "stage": "target",
        "message": "ConnectorUnavailableError: HTTP 503",
    }
    assert errored["verdict"] is None and errored["target_call"] is None


@pytest.mark.acceptance("T011-AC2")
def test_run_metadata_and_summary(report):
    assert report["report_version"] == "1"
    assert report["run"]["id"] == "abc123ef99"
    assert report["run"]["started_at"] == "2026-11-27T09:30:00+00:00"
    assert report["run"]["judgelab_version"] == "0.1.0"
    assert report["benchmark"] == {"id": "b1", "name": "Bench", "cases": 2}
    assert report["rubric"] == "semantic_correctness"
    assert report["connections"]["judge"] == {
        "provider": "openai_compatible",
        "model": "gpt-judge",
        "base_url": "https://api.openai.com/v1",
    }
    assert report["summary"] == {
        "total": 2,
        "passed": 1,
        "failed": 0,
        "errors": 1,
        "evaluated": 1,
        "pass_rate": 1.0,
        "coverage": 0.5,
    }


@pytest.mark.acceptance("T011-AC3")
def test_report_never_contains_a_secret(report, tmp_path):
    text = write_report(report, tmp_path).read_text(encoding="utf-8")
    assert SECRET not in text
    assert "REPORT_TEST_KEY" not in text


@pytest.mark.acceptance("T011-AC4")
def test_written_as_json_with_a_unique_name(report, tmp_path):
    path = write_report(report, tmp_path / "reports" / "nested")
    assert path.name == "run-20261127T093000Z-abc123ef.json"
    assert json.loads(path.read_text(encoding="utf-8")) == report
```

The `report` fixture builds one report that all four tests examine, which keeps each test short and focused on one criterion. There are two tricks in it.

The first is the fixed `START` and `END` times and the explicit `run_id="abc123ef99"`. Reports normally contain the current time and a random id, which would make the file name impossible to predict. Passing fixed values makes the test deterministic, so the AC4 test can check the exact name `run-20261127T093000Z-abc123ef.json`.

The second is the secrets test. The fixture uses `monkeypatch.setenv()` to put a fake key in a variable with a distinctive name, then creates a real `OpenAIConnector` that reads it. No request is ever sent, but the connector really does hold the key inside its SDK client. The report describes that connector as the judge, gets written to disk, and the test searches the *written text* for both the key and the variable name. Testing the file, and not the dictionary, means that nothing added during serialisation can slip past. `monkeypatch` removes the variable again when the test ends, and `tmp_path` gives each test its own empty directory that pytest cleans up for you. The AC4 test passes a directory two levels deep that doesn't exist yet, which is how it proves that `mkdir(parents=True)` works.

Finally, `json.loads(...) == report` proves the round trip: what you read back from the file is exactly the data you built.

## 9.10 Running the Tests

Run the whole suite:

```bash
$ uv run pytest
```

The acceptance-criteria table at the end should now show your eleven new criteria as passing. Here are the new rows and the end of the output (the earlier rows are omitted):

```text
PASS        T010-AC1   Totals for passed, failed and errored cases are counted in a single pa
PASS        T010-AC2   `pass_rate` is passed / (passed + failed): errors are never counted as
PASS        T010-AC3   `coverage` is the share of cases that reached a verdict, reported next
PASS        T011-AC1   Each case records its question, expected and actual answer, refusal, o
PASS        T011-AC2   The report records the run id, UTC start and finish times, JudgeLab ve
PASS        T011-AC3   The report never contains an API key or the name of the variable holdi
PASS        T011-AC4   Reports are written as UTF-8 JSON into an output directory (created if
PASS        T012-AC1   Every case goes to the target, then its answer goes to the judge; the 
PASS        T012-AC2   Target errors and truncated answers are ERROR at the target stage and 
PASS        T012-AC3   Judge errors are ERROR at the judge stage, never FAIL; a judge auth or
PASS        T012-AC4   A refusal from the target is sent to the judge as the answer, so the j
PASS        T014-AC1   The client is configured only from its arguments; a missing key variab
PASS        T014-AC2   A successful reply returns the text blocks joined (thinking blocks ski
PASS        T014-AC3   A `refusal` stop reason is returned as a refusal response, not an erro
PASS        T014-AC4   Truncation is reported the same way for every provider: `truncated` is
PASS        T014-AC5   A reply with no text and no refusal raises a response error.
PASS        T014-AC6   Failures map like the OpenAI connector's, including 402 billing and th
PASS        T014-AC7   The Claude connector passes the shared connector contract tests.
60 PASS
149 passed in 2.35s
```

Your timing will be different, but you should see 60 criteria passing and 149 tests.

## 9.11 Troubleshooting

- **`PackageNotFoundError: judgelab`** from `version("judgelab")`. The package isn't installed in the virtual environment, which can happen if you run Python from outside `uv`. Use `uv run pytest` and `uv run python`, which install the project before running anything.
- **`test_run_metadata_and_summary` fails on `judgelab_version`.** The test expects `0.1.0`. Check the `version` field in `pyproject.toml`.
- **`ImportError: cannot import name 'CaseResult' from partially initialized module`.** You have a circular import. `scoring.py` must not import from `runner.py` or `report.py`. The dependencies only go one way: `runner` and `report` import `scoring`, and `scoring` imports `benchmark`, `connectors` and `judge`.
- **`ValueError: 'PASS' is not a valid Outcome`.** Check the spelling of the values in `Outcome`. They must be exactly the same strings as in `Verdict`, because `Outcome(judgement.verdict)` converts by value.
- **The refusal test fails with `fake connector has no reply for prompt`.** The judge's scripted reply is keyed by the prompt, so the refusal must be formatted exactly as `[refused] <message>`, with one space.
- **`FileNotFoundError: benchmarks/sample.json`** in the Python session. Start `uv run python` from the root of the project, not from `src/` or `tests/`.

## 9.12 Exercises

1. In a Python session, call `evaluate()` with a fake judge whose `default` is `ConnectorAuthError("HTTP 401")`. How many prompts does the judge receive, and what do the error messages of the other cases say?
2. Build a `Summary(total=0, passed=0, failed=0, errors=0)` and read its three properties. Explain out loud why the pass rate is `None` but the coverage is `0.0`.
3. Write a test that proves the report keeps the target's answer for a case that was not judged because judging stopped. Which part of `_judge()` makes this work?
4. Without looking at the code, list the four checks that `_judge()` makes, in order, and say which stage each error is attributed to. Why does the truncation check come before the judge call and not after it?

## 9.13 Committing Your Work

Once all the tests pass, update the three task files. In T010 and T011, tick every acceptance criterion (`- [x]`), set **Status** to `Done`, fill in the **Branch** (`feat/p1-scoring-report-T010`) and set **AI-Assist** to `L4`. In T012, tick AC1 to AC4 only and set its Status to `In progress`, because the command line still has to be built in the next chapter.

Then stage and commit, following the commit conventions in [CONTRIBUTING.md](../../CONTRIBUTING.md):

```bash
$ git add src/judgelab/scoring.py src/judgelab/runner.py src/judgelab/report.py \
    tests/test_scoring.py tests/test_evaluate.py tests/test_report.py \
    docs/releases/v0.1/tasks/T010.md docs/releases/v0.1/tasks/T011.md \
    docs/releases/v0.1/tasks/T012.md
$ git commit
```

Here is a message you can adapt:

```text
feat(report): score outcomes and write the JSON report

Adds PASS/FAIL/ERROR outcomes and a summary whose pass rate is
passed / (passed + failed), so errors are reported next to the rate
and never counted as failures. evaluate() runs the target, then the
judge; target errors and truncated answers are never judged, and a
judge auth or quota error stops judging. The report records every
case's evidence and both connections without any credential.

Concepts: single-pass counting (O(n), works on one-shot iterators);
derived values as properties so they can't disagree with the counts.

AI-Assist: L4
```

Before you open the pull request, run the docs check, since this commit touches `docs/`:

```bash
$ python3 .claude/skills/vbench-docs/scripts/docids.py check
```

Then push the branch and ask Claude Code to open the pull request. The `vbench-pr` skill reads `CONTRIBUTING.md`, checks the branch, runs the readiness checklist and drafts the title and body for you to confirm. Under "How it was verified", paste the end of your `uv run pytest` output.

## 9.14 Wrapping Up

Congratulations, JudgeLab can now run a complete evaluation! Every case gets an outcome that says honestly whether a verdict exists, the summary keeps errors out of the pass rate while still reporting them as coverage, a broken judge reply can never turn into a failure, and the whole run is saved as a JSON report that a stranger could review and that never mentions your credentials.

The only way to run all of this, though, is to type Python into a session and build the connectors by hand. In the next codealong you are going to put a proper command line in front of it, with a YAML configuration file that names the target, the judge and the benchmark, so that a full evaluation becomes a single command: `judgelab run --config configs/evaluation.yaml`.
