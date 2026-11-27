"""Acceptance-criteria progress for the whole test suite.

Mark a test with the use-case acceptance criteria it verifies:

    @pytest.mark.acceptance("AC-001-01")
    def test_something(): ...

After every run, pytest prints every criterion defined in the use cases
(docs/usecases/*/README.md, written as **AC-001-01**: ...), grouped by use
case, with its status in that run.
"""

import re
from collections import defaultdict
from pathlib import Path

import pytest

USECASES_DIR = Path(__file__).resolve().parents[1] / "docs" / "usecases"
CRITERION = re.compile(r"\*\*(AC-\d{3}-\d{2,})\*\*:?\s*(.*)")
RESULTS = pytest.StashKey[dict]()


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "acceptance(*ids): use-case acceptance criteria verified by this test"
    )
    config.stash[RESULTS] = defaultdict(list)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    marker = item.get_closest_marker("acceptance")
    if marker and (report.when == "call" or report.outcome != "passed"):
        for criterion in marker.args:
            item.config.stash[RESULTS][criterion].append(report.outcome)
    return report


def defined_criteria() -> dict[str, dict[str, str]]:
    """{use case heading: {criterion id: description}}, in use-case order."""
    usecases = {}
    for readme in sorted(USECASES_DIR.glob("UC-*/README.md")):
        lines = readme.read_text(encoding="utf-8").splitlines()
        heading = lines[0].removeprefix("# ").strip() if lines else readme.parent.name
        criteria = {}
        for line in lines:
            match = CRITERION.search(line)
            if match:
                criteria[match.group(1)] = match.group(2).strip()
        usecases[heading] = criteria
    return usecases


def status_of(outcomes: list[str]) -> str:
    if not outcomes:
        return "not tested"
    if "failed" in outcomes:
        return "FAIL"
    if all(outcome == "passed" for outcome in outcomes):
        return "PASS"
    return "skipped"


def pytest_terminal_summary(terminalreporter, config):
    results = config.stash[RESULTS]
    usecases = defined_criteria()
    known = {criterion for criteria in usecases.values() for criterion in criteria}
    undefined = sorted(set(results) - known)
    if not known and not undefined:
        return
    counts = defaultdict(int)
    write = terminalreporter.write_line
    terminalreporter.write_sep("=", "acceptance criteria")
    for heading, criteria in usecases.items():
        if not criteria:
            continue
        statuses = {criterion: status_of(results.get(criterion, [])) for criterion in criteria}
        passing = sum(status == "PASS" for status in statuses.values())
        write(f"{heading}  ({passing}/{len(criteria)} passing)")
        for criterion, description in criteria.items():
            counts[statuses[criterion]] += 1
            write(f"  {statuses[criterion]:<11} {criterion}  {description[:60]}")
    for criterion in undefined:
        status = status_of(results[criterion])
        counts[status] += 1
        write(f"  {status:<11} {criterion}  (marked on a test but not defined in any use case)")
    write(
        " · ".join(
            f"{counts[s]} {s}" for s in ("PASS", "FAIL", "skipped", "not tested") if counts[s]
        )
    )
