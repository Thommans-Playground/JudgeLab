# Codealong 10: The Command Line

In this codealong you are going to give JudgeLab a front door. By the end you will have a `judgelab` command that reads a YAML configuration file naming the target model, the judge model, the benchmark and the rubric, runs the whole evaluation, prints its progress and a summary, and writes the JSON report from chapter 9. You will also have tests that run that command from end to end, report and all, without a single network call and without an API key.

The design idea of this chapter is a small one with a big payoff: the command line doesn't decide *how* connectors are built, it gets told. That one decision is what lets the tests swap the real connectors for fakes, and it is the "test doubles and dependency inversion" entry in your DSA ledger for T012.

> **AI-Assist level:** this is a guided codealong, so record your work as **L4**.

## 10.1 Before You Start

You need everything from chapter 9: `evaluate()` in `runner.py`, and the `scoring.py` and `report.py` modules, with a green test suite. Make sure the chapter 9 pull request is merged, then start a new topic branch from an up-to-date `main`:

```bash
$ git switch main && git pull --ff-only && git switch -c feat/p1-cli-T012
```

This chapter finishes task T012 (CLI and orchestration).

## 10.2 Writing the Acceptance Criteria First

Open [docs/releases/v0.1/tasks/T012.md](../../docs/releases/v0.1/tasks/T012.md). It already has AC1 to AC4 from the last chapter. Add these three lines right after T012-AC4:

_docs/releases/v0.1/tasks/T012.md_: New acceptance criteria

```markdown
- [ ] **T012-AC5**: `judgelab run --config <file>` runs the whole evaluation, prints progress and a summary, writes the report and exits 0.
- [ ] **T012-AC6**: Configuration problems (missing or invalid file, unknown settings, a pasted key, an unknown rubric, a missing dataset or API key) exit 1 with an `error:` message, no traceback and no report.
- [ ] **T012-AC7**: The config file names both connections, the dataset, the rubric and the output directory (default `reports`), and `--output-dir` overrides it.
```

Read AC6 again, because it describes most of the work in this chapter. A command line spends far more of its life rejecting bad input than running evaluations, and each rejection should be a short sentence you can act on, not a forty-line traceback.

## 10.3 The Configuration File

Configuration files are going to be written in YAML, which is easier on human eyes than JSON and allows comments. Python's standard library doesn't include a YAML parser, so let's add the `pyyaml` package:

```bash
$ uv add pyyaml
```

This adds a line to the `dependencies` list in `pyproject.toml`, and updates `uv.lock`, which you should commit along with it:

_pyproject.toml_: New dependency (added by `uv add`)

```toml
dependencies = [
    "anthropic>=2.14.0",
    "openai>=3.60.0",
    "pyyaml>=6.0.4",
]
```

Your version number may be newer. Now create a `configs` folder in the root of the project, with the configuration for your first real evaluation:

_configs/evaluation.yaml_: The bundled evaluation config

```yaml
# JudgeLab evaluation config. Secrets never go here: only the NAME of the
# environment variable that holds each key.
connections:
  target:
    provider: openai_compatible
    model: gpt-6.2-astra
    api_key_env: OPENAI_API_KEY
    timeout_s: 60
  judge:
    provider: anthropic
    model: claude-opus-5-5
    api_key_env: ANTHROPIC_API_KEY
    timeout_s: 300
    options:
      max_tokens: 16000

benchmark:
  dataset: benchmarks/sample.json
  rubric: semantic_correctness

output:
  dir: reports
```

Each block under `connections` is exactly the dictionary that `ConnectionProfile.from_dict()` has accepted since chapter 5, so all of its validation applies here for free. The target is an OpenAI model and the judge is a Claude model. Using a different provider for the judge is a deliberate choice: a model judging its own family's answers may be more lenient with them, and keeping the two separate makes that one less thing to worry about. If you've been using a different model id in your `.env` file, put that one here instead.

Notice that the file only names the environment variables, never the keys themselves. This file is going to be committed to Git, and anything committed should be safe to show anyone.

The `output.dir` setting says where the reports go. Reports are generated artifacts, and [CONTRIBUTING.md](../../CONTRIBUTING.md) says those should never be committed, so let's tell Git to ignore the folder. Open `.gitignore` and add these lines right after the "Scratch API replies" block:

_.gitignore_: Ignore generated reports

```text
# Evaluation reports (copy the ones you keep as evidence into docs/)
reports/
```

The comment is a reminder for chapter 11, when you are going to keep some reports as evidence for the release.

## 10.4 Loading the Configuration

The next step is a module that turns the YAML file into a validated Python object, or explains clearly why it can't.

_src/judgelab/config.py_: Loading the evaluation config

```python
"""Evaluation configuration, loaded from a YAML file."""

from dataclasses import dataclass
from pathlib import Path

import yaml

from judgelab.connectors import ConnectionProfile, ProfileError

SECTIONS = {"connections", "benchmark", "output"}


class ConfigError(ValueError):
    """The configuration file is missing or invalid."""


@dataclass(frozen=True)
class EvaluationConfig:
    target: ConnectionProfile
    judge: ConnectionProfile
    dataset: Path
    rubric: str
    output_dir: Path


def load_config(path: str | Path) -> EvaluationConfig:
    """Load an evaluation config. Relative paths are relative to the working directory."""
    path = Path(path)
    try:
        # safe_load builds only plain data (dicts, lists, strings, numbers):
        # unlike yaml.load, a config file can never make it run code.
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"config file not found: {path}") from None
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        where = f" (line {mark.line + 1}, column {mark.column + 1})" if mark else ""
        raise ConfigError(f"{path} is not valid YAML{where}") from None

    if not isinstance(data, dict):
        raise ConfigError(f"{path}: expected sections {', '.join(sorted(SECTIONS))}")
    unknown = sorted(set(data) - SECTIONS)
    if unknown:
        raise ConfigError(f"{path}: unknown section(s) {', '.join(unknown)}")

    connections = _section(data, "connections", path)
    benchmark = _section(data, "benchmark", path)
    output = data.get("output") or {}
    try:
        target = ConnectionProfile.from_dict("target", connections.get("target"))
        judge = ConnectionProfile.from_dict("judge", connections.get("judge"))
    except ProfileError as e:
        raise ConfigError(f"{path}: {e}") from None

    dataset, rubric = benchmark.get("dataset"), benchmark.get("rubric")
    if not isinstance(dataset, str) or not dataset.strip():
        raise ConfigError(f"{path}: benchmark.dataset must be a file path")
    if not isinstance(rubric, str) or not rubric.strip():
        raise ConfigError(f"{path}: benchmark.rubric must be a rubric id")
    output_dir = output.get("dir", "reports") if isinstance(output, dict) else None
    if not isinstance(output_dir, str) or not output_dir.strip():
        raise ConfigError(f"{path}: output.dir must be a directory path")

    return EvaluationConfig(target, judge, Path(dataset), rubric, Path(output_dir))


def _section(data: dict, name: str, path: Path) -> dict:
    section = data.get(name)
    if not isinstance(section, dict):
        raise ConfigError(f"{path}: missing or invalid section {name!r}")
    return section
```

The most important line in this file is the one with the comment above it. PyYAML has two ways to read a document. `yaml.load()` with its full loader understands special tags that build arbitrary Python objects, and a tag like `!!python/object/apply:os.system` tells it to *call a function* while loading. A configuration file that runs shell commands when you open it is a terrible thing to have in an evaluation tool, because sooner or later someone will hand you a config file to try. `yaml.safe_load()` only builds plain data: dictionaries, lists, strings, numbers, booleans and `None`. When it meets one of those dangerous tags, it raises an error instead. So the rule in JudgeLab is simple: always `safe_load`, never `load`. You are going to see this in action in section 10.7.

Next, look at how YAML errors are reported. PyYAML's exceptions carry a `problem_mark` with the line and column where parsing went wrong, but those are counted from zero, and editors count from one, hence the `+ 1`. Not every YAML error has a mark, so `getattr()` with a default of `None` handles both cases. The `from None` at the end of each `raise` drops the original exception from the chain. Its message is long and repeats chunks of the file, and the short message is all the user needs.

Then the structure is checked. An empty file loads as `None`, and a file with just a list loads as a list, so the first check makes sure there is a dictionary of sections at all. Then any section that isn't one of the three known ones is rejected. This is the same "unknown settings are errors" rule you applied to profiles and benchmark files: a section called `benchmarks:` or `ouput:` would otherwise be silently ignored, and you'd spend an afternoon wondering why your setting had no effect.

The two connection blocks are handed to `ConnectionProfile.from_dict()`, which already knows how to validate them, including spotting a key pasted into `api_key_env`. Its `ProfileError` is caught and re-raised as a `ConfigError` with the file name in front. That way the command line only has one configuration error type to deal with, and the message tells you which file the problem is in as well as which connection.

The `output` section is optional, so a missing one becomes an empty dictionary, and a missing `dir` becomes `"reports"`. If `output` exists but isn't a dictionary (say, `output: reports` written by mistake), `output_dir` becomes `None` and the next check rejects it.

Finally, a word about paths, since the docstring makes a promise about them. `Path(dataset)` is used exactly as written, so `benchmarks/sample.json` means "relative to the folder you ran the command from", not "relative to the config file". That's the behaviour most command line tools have, and it means you should run `judgelab` from the root of the project.

## 10.5 The Command Line

Now for the command itself. Python's standard library includes `argparse`, which handles the parsing, the `--help` output and the usage errors for you.

_src/judgelab/cli.py_: The `judgelab` command line

```python
"""The `judgelab` command line."""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from judgelab.benchmark import BenchmarkError, load_benchmark
from judgelab.config import ConfigError, load_config
from judgelab.connectors import (
    ConnectionProfile,
    ConnectorError,
    ModelConnector,
    ProfileError,
    create_connector,
)
from judgelab.judge import Judge, JudgeError, get_rubric
from judgelab.report import RunInfo, build_report, utc_now, write_report
from judgelab.runner import evaluate
from judgelab.scoring import CaseResult, Summary, summarise

ConnectorFactory = Callable[[ConnectionProfile], ModelConnector]


def main(
    argv: list[str] | None = None, *, connector_factory: ConnectorFactory = create_connector
) -> int:
    """Entry point. Returns the process exit code: 0 completed, 1 could not start."""
    parser = argparse.ArgumentParser(
        prog="judgelab", description="Evaluate a model against a benchmark."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="run an evaluation from a config file")
    run.add_argument("--config", type=Path, required=True, help="evaluation config (YAML)")
    run.add_argument(
        "--output-dir", type=Path, help="where to write the report (overrides the config)"
    )
    args = parser.parse_args(argv)
    return run_command(args.config, args.output_dir, connector_factory)


def run_command(
    config_path: Path, output_dir: Path | None, connector_factory: ConnectorFactory
) -> int:
    try:
        config = load_config(config_path)
        benchmark = load_benchmark(config.dataset)
        rubric = get_rubric(config.rubric)
        target = connector_factory(config.target)
        judge_connector = connector_factory(config.judge)
    except (ConfigError, ProfileError, BenchmarkError, JudgeError, ConnectorError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    total = len(benchmark.cases)
    print(f"Running {benchmark.name!r}: {total} cases")
    print(f"  target: {target.provider} {target.model}")
    print(f"  judge:  {judge_connector.provider} {judge_connector.model} (rubric {rubric.id})")

    done = 0

    def show_progress(result: CaseResult) -> None:
        nonlocal done
        done += 1
        detail = f"  ({result.error_stage}: {result.error})" if result.error else ""
        print(f"[{done}/{total}] {result.case.id}: {result.outcome}{detail}")

    started = utc_now()
    results = evaluate(benchmark, target, Judge(judge_connector, rubric), on_result=show_progress)
    finished = utc_now()

    summary = summarise(results)
    run = RunInfo(benchmark, rubric.id, target, judge_connector, started, finished)
    path = write_report(build_report(run, results, summary), output_dir or config.output_dir)
    print_summary(summary)
    print(f"Report: {path}")
    return 0


def print_summary(summary: Summary) -> None:
    print(
        f"Passed: {summary.passed}  Failed: {summary.failed}  Errors: {summary.errors}  "
        f"(of {summary.total})"
    )
    if summary.pass_rate is None:
        print("Pass rate: n/a (no case reached a verdict)")
    else:
        print(
            f"Pass rate: {summary.pass_rate:.1%} of {summary.evaluated} evaluated  "
            f"Coverage: {summary.coverage:.1%}"
        )


if __name__ == "__main__":
    sys.exit(main())
```

There's a lot here, so let's take it in pieces, starting with the most important one.

**Dependency injection.** Look at the signature of `main()`. Besides the arguments, it accepts a `connector_factory`: a function that takes a `ConnectionProfile` and returns a `ModelConnector`. The `ConnectorFactory` type alias at the top gives that idea a name. In normal use, nobody passes it, so the default, the real `create_connector()` from chapter 5, builds real connectors that talk to real models. But a test can pass its own factory that returns `FakeConnector`s, and then the *entire* command, from argument parsing to the report file, runs with no network and no keys.

This is what "dependency inversion" means in practice. The command line depends on the abstract idea of "something that makes connectors", not on the concrete registry, and whoever calls `main()` decides which one it gets. Passing the dependency in as an argument is called "dependency injection", and it's the simplest form of it there is: no framework, just a keyword argument with a sensible default. The `*` makes it keyword-only, so it can never be passed by accident as the second positional argument.

**`main()` versus `run_command()`.** `main()` deals with the command line: it builds the parser, reads the arguments, and hands plain values to `run_command()`. `run_command()` knows nothing about `argparse`. Calling `parser.parse_args(argv)` with `argv=None` makes `argparse` read `sys.argv`, which is what happens when you type the command in a terminal, while the tests pass a list like `["run", "--config", "x.yaml"]`.

The parser uses a subcommand, `run`, even though there's only one for now. `add_subparsers(..., required=True)` makes `judgelab` with no subcommand a usage error. Starting with subcommands means that later commands (comparing two reports, say) can be added next to `run` without changing how anyone calls it.

**Exit codes.** A command line communicates with scripts and CI pipelines through its exit code. This one has three:

- `0`: the evaluation ran and the report was written. Note that this is true even if every case failed! A failing model is a *result*, not a crash, and the report is where the results go.
- `1`: the evaluation couldn't start, because of a configuration problem.
- `2`: the command was used incorrectly, for example `--config` is missing. You don't have to write any code for this one: `argparse` prints the usage message and exits with 2 on its own, which is the Unix convention for usage errors.

**Failing before anything happens.** Everything that can be wrong with a configuration is checked in the single `try` block at the start of `run_command()`: the file, the benchmark, the rubric and both connectors. Building a connector reads its API key, so a missing key is caught here too. Only once all of that has worked does the command print anything or make a single call. This means a typo in the judge's model settings is reported in a fraction of a second, instead of after the target has answered every question and you have paid for it.

The `except` clause lists the five JudgeLab error types that mean "bad configuration", and nothing else. It prints `error:` and the message to standard error and returns 1, with no traceback. Every one of those messages was designed in an earlier chapter to never include a secret: connector errors name the missing variable but never show a value, and the profile check refuses a pasted key without repeating it. That's what makes it safe to print them. Anything else, such as a `TypeError` from a bug, is deliberately *not* caught, so it shows up with its full traceback, the same rule you followed in `run_target()` in chapter 7.

**Progress with a closure.** `show_progress()` is defined inside `run_command()` so that it can see `total`. It also needs to count how many results it has seen, and that count must survive between calls. The `nonlocal done` statement tells Python that `done` is the variable from the enclosing function. Without it, `done += 1` would create a brand new local variable inside `show_progress()` and fail with `UnboundLocalError`. A function that carries some of its surrounding variables around with it is called a closure, and it's a lightweight alternative to writing a small class with a counter attribute.

Each progress line shows the outcome, and for errors, the stage and the message in parentheses. The outcome prints as `PASS` rather than `Outcome.PASS` because `Outcome` is a `StrEnum`. Since `evaluate()` collects all the target's answers before judging, the progress lines only start to appear once the target stage is finished, and then they come one per judged case.

**The summary.** `print_summary()` prints the counts, then either the pass rate with coverage or, when nothing was evaluated, `n/a` with the reason. The `:.1%` format multiplies by 100 and adds the percent sign, so `0.8` prints as `80.0%`. The pass rate always says how many cases it was computed from ("of 5 evaluated"), so a reader can't mistake a 100% pass rate over one case for a 100% pass rate over fifty.

The last two lines let you run the module directly with `python -m judgelab.cli`, and `sys.exit()` turns the return value of `main()` into the exit code.

## 10.6 Registering the Command

Typing `python -m judgelab.cli run ...` works, but it is not much of a command. Let's give it a proper name. Open `pyproject.toml` and add this section right after the `dependencies` list:

_pyproject.toml_: The `judgelab` command

```toml
[project.scripts]
judgelab = "judgelab.cli:main"
```

This tells the packaging tools to create an executable called `judgelab` in the virtual environment that imports `judgelab.cli` and calls `main()`, passing its return value to `sys.exit()`. The next time you use `uv run`, it notices that `pyproject.toml` changed and reinstalls the project, so the command exists from then on.

## 10.7 Trying It Out

Let's see what the command looks like from the outside. Start with the help messages:

```bash
$ uv run judgelab --help
usage: judgelab [-h] {run} ...

Evaluate a model against a benchmark.

positional arguments:
  {run}
    run       run an evaluation from a config file

options:
  -h, --help  show this help message and exit
$ uv run judgelab run --help
usage: judgelab run [-h] --config CONFIG [--output-dir OUTPUT_DIR]

options:
  -h, --help            show this help message and exit
  --config CONFIG       evaluation config (YAML)
  --output-dir OUTPUT_DIR
                        where to write the report (overrides the config)
```

You got all of that from `argparse`, without writing a single `print()`. Now try a usage error, and check the exit code with `echo $?`:

```bash
$ uv run judgelab run
usage: judgelab run [-h] --config CONFIG [--output-dir OUTPUT_DIR]
judgelab run: error: the following arguments are required: --config
$ echo $?
2
```

Next, run the real configuration. You have a `.env` file with your OpenAI key in it, but `uv run` doesn't read `.env` files unless you ask it to, so the key is not in the environment. To be completely sure that nothing reaches a real model, I'm going to remove both variables for this one command with `env -u`:

```bash
$ env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY uv run judgelab run --config configs/evaluation.yaml
error: environment variable OPENAI_API_KEY is not set
$ echo $?
1
```

That's one line, naming the variable, with no traceback and no report. Let's try some broken configuration files too. Copy `configs/evaluation.yaml` to `sandbox/pasted.yaml`, and in the copy, change the target's `api_key_env: OPENAI_API_KEY` line to `api_key_env: sk-proj-abc123`, as if someone had pasted a key there by mistake. Then create `sandbox/bad.yaml` with a single line containing `connections: [`, and `sandbox/evil.yaml` with this line:

```yaml
connections: !!python/object/apply:os.system ['echo hacked']
```

Now run all three:

```bash
$ uv run judgelab run --config sandbox/pasted.yaml
error: sandbox/pasted.yaml: connection 'target': api_key_env must name an environment variable (like OPENAI_API_KEY), not contain a key
$ uv run judgelab run --config sandbox/bad.yaml
error: sandbox/bad.yaml is not valid YAML (line 2, column 1)
$ uv run judgelab run --config sandbox/evil.yaml
error: sandbox/evil.yaml is not valid YAML (line 1, column 14)
```

The pasted key is refused without being repeated back. The unclosed bracket is reported at line 2, column 1, which is where the parser ran out of file while it was still waiting for the `]`. And the third file, which would have run `echo hacked` with `yaml.load()`, was rejected by `safe_load()`, and nothing was executed. Delete the three sandbox files when you're done.

## 10.8 A Full Run Without the Network

You haven't seen a successful run yet, and I don't want you to spend money on one until the next chapter. But you already have everything you need to see one for free: `main()` accepts a connector factory, so let's write a small script that passes it one that builds fakes.

_sandbox/fake_run.py_: The real CLI with fake connectors

```python
"""Run the real CLI with fake connectors (no keys, no network)."""
import sys
from judgelab.benchmark import load_benchmark
from judgelab.cli import main
from judgelab.connectors import FakeConnector
from judgelab.judge import build_judge_prompt

cases = {c.id: c for c in load_benchmark("benchmarks/sample.json").cases}
answers = {"gk-001": "Paris", "gk-002": "Au", "gk-003": "Charlotte Bronte", "gk-004": "6", "gk-005": "Jupiter"}
PASS = '{"verdict": "PASS", "justification": "The answer matches the expected answer."}'
FAIL = '{"verdict": "FAIL", "justification": "Pride and Prejudice was written by Jane Austen, not Charlotte Bronte."}'

def factory(profile):
    if profile.name == "target":
        return FakeConnector(model=profile.model, replies={cases[i].question: a for i, a in answers.items()})
    return FakeConnector(model=profile.model, default=PASS,
                         replies={build_judge_prompt(cases["gk-003"], "Charlotte Bronte"): FAIL})

sys.exit(main(sys.argv[1:], connector_factory=factory))
```

The factory receives each `ConnectionProfile` from the real config file and builds a `FakeConnector` with the same model name. The fake target gets one answer wrong, and the fake judge is scripted to fail that answer and pass the rest. The last line hands the script's own arguments to `main()`. Ruff may reformat this file when you save it, and that's fine. It is a playground script, so it lives in `sandbox/`.

Run it with the same arguments you'd give the real command:

```bash
$ uv run python sandbox/fake_run.py run --config configs/evaluation.yaml
Running 'General knowledge (sample)': 5 cases
  target: fake gpt-6.2-astra
  judge:  fake claude-opus-5-5 (rubric semantic_correctness)
[1/5] gk-001: PASS
[2/5] gk-002: PASS
[3/5] gk-003: FAIL
[4/5] gk-004: PASS
[5/5] gk-005: PASS
Passed: 4  Failed: 1  Errors: 0  (of 5)
Pass rate: 80.0% of 5 evaluated  Coverage: 100.0%
Report: reports/run-20261127T093000Z-3f9c2a1b.json
```

Your report name will have a different time and id. This is the real command line: the real config loader, the real benchmark, the real `evaluate()` and the real report writer. Only the connectors are fake. Notice that the provider shows up as `fake`, both here and in the report's `connections` section, so a fake run can never be mistaken for a real one later on. Open the report and find `gk-003`, and you'll see the wrong answer, the judge's justification, and both calls recorded, exactly as in chapter 9.

This script does exactly what the tests in the next section do, except that the tests check the output automatically.

## 10.9 Tests

Here is the test file for the command line.

_tests/test_cli.py_: End-to-end CLI tests

```python
"""End-to-end CLI tests with fake connectors injected through `connector_factory`."""

import json
from pathlib import Path

import pytest

from judgelab.benchmark import load_benchmark
from judgelab.cli import main
from judgelab.config import load_config
from judgelab.connectors import FakeConnector
from judgelab.judge import build_judge_prompt

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "benchmarks" / "sample.json"

CONFIG = """
connections:
  target: {provider: openai_compatible, model: target-model, api_key_env: TARGET_KEY}
  judge: {provider: anthropic, model: judge-model, api_key_env: JUDGE_KEY}
benchmark:
  dataset: SAMPLE
  rubric: semantic_correctness
output:
  dir: OUT
"""
PASS = '{"verdict": "PASS", "justification": "Correct."}'
FAIL = '{"verdict": "FAIL", "justification": "Wrong."}'


def write_config(tmp_path, text=CONFIG):
    path = tmp_path / "evaluation.yaml"
    path.write_text(text.replace("SAMPLE", str(SAMPLE)).replace("OUT", str(tmp_path / "reports")))
    return path


FRANCE = load_benchmark(SAMPLE).cases[0]


def fake_factory(profile):
    """Builds fakes instead of real connectors: the target always says 'Paris'."""
    if profile.name == "target":
        return FakeConnector(model=profile.model, default="Paris")
    # The judge passes the France question and fails everything else.
    return FakeConnector(
        model=profile.model, default=FAIL, replies={build_judge_prompt(FRANCE, "Paris"): PASS}
    )


@pytest.mark.acceptance("T012-AC5")
def test_run_end_to_end(tmp_path, capsys):
    exit_code = main(
        ["run", "--config", str(write_config(tmp_path))], connector_factory=fake_factory
    )
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Running 'General knowledge (sample)': 5 cases" in out
    assert "[1/5] gk-001: PASS" in out
    assert "[5/5] gk-005: FAIL" in out
    assert "Passed: 1  Failed: 4  Errors: 0  (of 5)" in out
    assert "Pass rate: 20.0% of 5 evaluated  Coverage: 100.0%" in out
    reports = list((tmp_path / "reports").glob("run-*.json"))
    assert len(reports) == 1
    assert f"Report: {reports[0]}" in out
    report = json.loads(reports[0].read_text())
    assert report["summary"]["passed"] == 1
    assert report["connections"]["target"]["model"] == "target-model"


@pytest.mark.acceptance("T012-AC7")
def test_output_dir_option_overrides_the_config(tmp_path, capsys):
    elsewhere = tmp_path / "elsewhere"
    args = ["run", "--config", str(write_config(tmp_path)), "--output-dir", str(elsewhere)]
    assert main(args, connector_factory=fake_factory) == 0
    assert len(list(elsewhere.glob("run-*.json"))) == 1


@pytest.mark.acceptance("T012-AC7")
def test_config_defines_both_connections_dataset_rubric_and_output(tmp_path):
    config = load_config(write_config(tmp_path))
    assert (config.target.provider, config.judge.provider) == ("openai_compatible", "anthropic")
    assert (config.target.api_key_env, config.judge.api_key_env) == ("TARGET_KEY", "JUDGE_KEY")
    assert (config.dataset, config.rubric) == (SAMPLE, "semantic_correctness")
    assert config.output_dir == tmp_path / "reports"


@pytest.mark.acceptance("T012-AC7")
def test_output_dir_defaults_to_reports(tmp_path):
    text = CONFIG.split("output:")[0]
    assert load_config(write_config(tmp_path, text)).output_dir == Path("reports")


@pytest.mark.acceptance("T012-AC7")
def test_the_bundled_config_is_valid():
    config = load_config(ROOT / "configs" / "evaluation.yaml")
    assert (config.target.provider, config.judge.provider) == ("openai_compatible", "anthropic")


@pytest.mark.acceptance("T012-AC6")
@pytest.mark.parametrize(
    "text, message",
    [
        ("connections: [", "is not valid YAML (line 1, column 15)"),
        ("connections: {}\nbenchmark: {}\nextras: {}\n", "unknown section(s) extras"),
        (CONFIG.replace("model: target-model", "modle: target-model"), "unknown setting(s) modle"),
        (CONFIG.replace("TARGET_KEY", "sk-pasted-key"), "must name an environment variable"),
        (CONFIG.replace("semantic_correctness", "strict"), "unknown rubric 'strict'"),
        (CONFIG.replace("SAMPLE", "missing.json"), "missing.json"),
    ],
    ids=["bad-yaml", "unknown-section", "typo", "pasted-key", "unknown-rubric", "no-dataset"],
)
def test_configuration_problems_exit_1_without_a_traceback(tmp_path, capsys, text, message):
    path = tmp_path / "evaluation.yaml"
    path.write_text(text.replace("SAMPLE", str(SAMPLE)).replace("OUT", str(tmp_path / "reports")))
    assert main(["run", "--config", str(path)], connector_factory=fake_factory) == 1
    err = capsys.readouterr().err
    assert err.startswith("error: ")
    assert message in err
    assert "Traceback" not in err
    assert "sk-pasted-key" not in err
    assert not (tmp_path / "reports").exists()


@pytest.mark.acceptance("T012-AC6")
def test_missing_config_file(tmp_path, capsys):
    assert main(["run", "--config", str(tmp_path / "nope.yaml")]) == 1
    assert "config file not found" in capsys.readouterr().err


@pytest.mark.acceptance("T012-AC6")
def test_missing_api_key_is_reported_before_running(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("TARGET_KEY", raising=False)
    assert main(["run", "--config", str(write_config(tmp_path))]) == 1  # real factory
    assert "environment variable TARGET_KEY is not set" in capsys.readouterr().err
```

Let's look at the techniques.

**`fake_factory` is the test double.** It has the same shape as `create_connector()`, a function from a profile to a connector, so `main()` can't tell the difference. The fake target says "Paris" to every question, and the fake judge passes only the France question. With five questions, that gives a predictable 1 pass and 4 failures, which is exactly what `test_run_end_to_end` checks. Notice that the profile's `api_key_env` names, `TARGET_KEY` and `JUDGE_KEY`, are never set anywhere. The fakes never read them, and that's the point.

**A config template with placeholders.** The `CONFIG` string uses YAML's compact `{key: value}` form to keep each connection on one line, and contains two placeholders. `write_config()` replaces `SAMPLE` with the absolute path to the real sample benchmark and `OUT` with a folder inside `tmp_path`, so every test writes its reports into its own temporary directory and never into your project. Several tests then derive variations from the template with `str.replace()`, which keeps each broken config one line long.

**`capsys` captures the output.** `capsys` is a built-in pytest fixture that captures everything printed to standard output and standard error during the test. `capsys.readouterr()` returns both as strings, in `.out` and `.err`, so the tests can check the exact progress lines and that errors go to `stderr`.

**A parametrized table of failures.** `test_configuration_problems_exit_1_without_a_traceback` is one test function that pytest runs six times, once per `(text, message)` pair. The `ids` give each run a readable name, so a failure shows up as `test_configuration_problems_exit_1_without_a_traceback[pasted-key]` instead of `[text3-message3]`. Each run checks the same five promises from AC6: exit code 1, an `error:` prefix, a useful message, no traceback, and no report folder. It also checks that the pasted key never appears in the error, in every case, not only in the one where a key was pasted. Adding a new kind of failure later is a one-line change to the table.

**Using the real factory when it's safe.** The last two tests call `main()` *without* a factory, so the real `create_connector()` is used. That's safe here because both fail before any request is possible: one has no config file, and in the other, `monkeypatch.delenv()` makes sure `TARGET_KEY` is not set, so building the connector raises an auth error. This proves that the real path reports a missing key cleanly too.

**Testing the file you ship.** `test_the_bundled_config_is_valid` loads the actual `configs/evaluation.yaml`. It's a tiny test, but without it, a typo in the shipped config would only be discovered by the first person who runs it, which in chapter 11 is going to be you, with your API keys.

## 10.10 Running the Tests

Run the suite:

```bash
$ uv run pytest
```

All seven T012 criteria should now be passing. Here are the T012 rows and the end of the output:

```text
PASS        T012-AC1   Every case goes to the target, then its answer goes to the judge; the 
PASS        T012-AC2   Target errors and truncated answers are ERROR at the target stage and 
PASS        T012-AC3   Judge errors are ERROR at the judge stage, never FAIL; a judge auth or
PASS        T012-AC4   A refusal from the target is sent to the judge as the answer, so the j
PASS        T012-AC5   `judgelab run --config <file>` runs the whole evaluation, prints progr
PASS        T012-AC6   Configuration problems (missing or invalid file, unknown settings, a p
PASS        T012-AC7   The config file names both connections, the dataset, the rubric and th
PASS        T014-AC1   The client is configured only from its arguments; a missing key variab
PASS        T014-AC2   A successful reply returns the text blocks joined (thinking blocks ski
PASS        T014-AC3   A `refusal` stop reason is returned as a refusal response, not an erro
PASS        T014-AC4   Truncation is reported the same way for every provider: `truncated` is
PASS        T014-AC5   A reply with no text and no refusal raises a response error.
PASS        T014-AC6   Failures map like the OpenAI connector's, including 402 billing and th
PASS        T014-AC7   The Claude connector passes the shared connector contract tests.
63 PASS
162 passed in 2.52s
```

That's 63 criteria and 162 tests, and not one of them touched the network.

## 10.11 Troubleshooting

- **``error: Failed to spawn: `judgelab` ``**, or **`command not found: judgelab`**. The `[project.scripts]` section is missing or misspelled, or the project hasn't been reinstalled since you added it. Check the section in `pyproject.toml` and run `uv sync`. Also remember that the command only exists inside the virtual environment, so you must run it as `uv run judgelab`.
- **`ModuleNotFoundError: No module named 'yaml'`.** The package is called `pyyaml`, but the module you import is `yaml`. Run `uv add pyyaml`, not `uv add yaml`.
- **`error: invalid benchmark benchmarks/sample.json:` followed by `- file not found`.** Relative paths in the config are relative to the folder you run the command from. Run it from the root of the project.
- **`UnboundLocalError: cannot access local variable 'done'`.** You forgot the `nonlocal done` line in `show_progress()`.
- **The `bad-yaml` test reports a different line or column.** The test writes `connections: [` without a newline at the end, so the parser runs out of input at line 1, column 15. When you typed the same thing into a file in your editor, it most likely added a newline, which is why you saw line 2 in section 10.7. Both are correct.
- **The run starts calling real models when you didn't expect it to.** Your keys are exported in your shell profile. Use `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY` in front of the command, as in section 10.7, or remove the exports and keep the keys only in `.env`.

## 10.12 Exercises

1. Write a connector factory in `sandbox/fake_run.py` that makes the fake judge raise `ConnectorAuthError("HTTP 401")` for every prompt. Run it, and look at the progress lines, the summary and the report. Which line of `print_summary()` produced the pass rate line, and why?
2. The command currently only reports judged cases. Pass an `on_target` callback to `evaluate()` in `run_command()` so that it also prints a line as each target answer arrives. Run the fake script to see it, then put the code back the way it was.
3. Run `uv run python -m judgelab.cli run --help`. Why does this work even without the `[project.scripts]` section?
4. Explain out loud why `main()` takes a `connector_factory` argument, and what the tests would have to do without it. Which entry in your DSA ledger does this put into practice?

## 10.13 Committing Your Work

Once the tests pass, update [T012](../../docs/releases/v0.1/tasks/T012.md): tick AC5 to AC7, set **Status** to `Done`, fill in **Branch** and set **AI-Assist** to `L4`. Then commit. The new dependency, the lock file, the config, the code and the tests form one logical change, so they go in one commit. `sandbox/fake_run.py` is a playground script, so leave it out.

```bash
$ git add pyproject.toml uv.lock .gitignore configs/evaluation.yaml \
    src/judgelab/config.py src/judgelab/cli.py tests/test_cli.py \
    docs/releases/v0.1/tasks/T012.md
$ git commit
```

A message you can adapt:

```text
feat(orchestrator): add judgelab run command with a YAML config

The judgelab command loads a config naming the target and judge
connections, the dataset, the rubric and the output directory, runs
the evaluation, prints progress and a summary, and writes the report.
Configuration problems exit 1 with a one-line error, before any model
is called.

Configs are read with yaml.safe_load so a config file can never run
code. The connector factory is injected into main(), so the tests run
the whole CLI end to end with fake connectors and no network.

AI-Assist: L4
```

Run `python3 .claude/skills/vbench-docs/scripts/docids.py check`, push the branch, and ask Claude Code to open the pull request with the `vbench-pr` skill. Include the fake run transcript from section 10.8 under "How it was verified", along with your test results.

## 10.14 Wrapping Up

Congratulations, JudgeLab is now a real tool! One command reads a configuration you can safely commit, rejects every kind of bad configuration with a single clear line before spending anything, runs the whole evaluation, and leaves a report behind. And because the command takes its connector factory as an argument, you have proven all of that end to end without a network connection.

There is only one thing left to do, and it's the one this whole project has been building towards: point JudgeLab at real models and see what happens. In the next codealong you are going to add live smoke tests, run your first real evaluation, review its report as a human, and then release v0.1.
