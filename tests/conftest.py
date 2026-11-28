"""Acceptance-criteria progress for the whole test suite.

Mark a test with the use-case acceptance criteria it verifies:

    @pytest.mark.acceptance("AC-001-01")
    def test_something(): ...

After every run, pytest prints every criterion defined in the use cases
(docs/usecases/UC-*/*.feature, one Gherkin Scenario per criterion, tagged
@AC-001-01), grouped by use case, with its status in that run.
"""

import re
from collections import defaultdict
from pathlib import Path

import pytest

USECASES_DIR = Path(__file__).resolve().parents[1] / "docs" / "usecases"
TAG = re.compile(r"@(AC-\d{3}-\d{2,})")
SCENARIO = re.compile(r"^\s*Scenario(?: Outline)?:\s*(.*)")
RESULTS = pytest.StashKey[dict]()
STATUS_ORDER = ("PASS", "FAIL", "skipped", "not tested")
STATUS_COLORS = {
    "PASS": {"green": True},
    "FAIL": {"red": True, "bold": True},
    "skipped": {"yellow": True},
    "not tested": {"light": True},
}


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
    """{use case heading: {criterion id: description}}, in use-case order.

    A criterion is an @AC-... tag; its description is the title of the
    Scenario that follows the tag. Scenarios tagged @retired are left out.
    """
    usecases = {}
    for feature in sorted(USECASES_DIR.glob("UC-*/*.feature")):
        heading = feature.parent.name
        criteria = {}
        tagged, retired = [], False
        for line in feature.read_text(encoding="utf-8").splitlines():
            if line.startswith("Feature:"):
                heading = line.removeprefix("Feature:").strip()
            elif line.lstrip().startswith("@"):
                tagged += TAG.findall(line)
                retired = retired or "@retired" in line.split()
            elif match := SCENARIO.match(line):
                if not retired:
                    for criterion in tagged:
                        criteria[criterion] = match.group(1).strip()
                tagged, retired = [], False
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
    write = terminalreporter.write

    def criterion_line(status, criterion, description):
        counts[status] += 1
        write("  ")
        write(f"{status:<11}", **STATUS_COLORS[status])
        write(f" {criterion}  {description}\n")

    terminalreporter.write_sep("=", "acceptance criteria")
    for heading, criteria in usecases.items():
        if not criteria:
            continue
        statuses = {criterion: status_of(results.get(criterion, [])) for criterion in criteria}
        passing = sum(status == "PASS" for status in statuses.values())
        write(heading, bold=True)
        write(f"  ({passing}/{len(criteria)} passing)\n")
        for criterion, description in criteria.items():
            criterion_line(statuses[criterion], criterion, description[:60])
    for criterion in undefined:
        description = "(marked on a test but not defined in any use case)"
        criterion_line(status_of(results[criterion]), criterion, description)
    totals = [status for status in STATUS_ORDER if counts[status]]
    for i, status in enumerate(totals):
        write(f"{counts[status]} {status}", **STATUS_COLORS[status])
        write(" · " if i < len(totals) - 1 else "\n")
