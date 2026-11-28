#!/usr/bin/env python3
"""Map acceptance criteria to the tests that claim to verify them.

Reads every Scenario in docs/usecases/UC-*/*.feature (tagged @AC-UUU-NN) and
every test function marked @pytest.mark.acceptance(...) under tests/, and
prints, per criterion: the full Scenario text, then each marked test with its
file:line and number of parametrized cases. Standard library only.

    python3 acmap.py                 # every criterion that has a marked test
    python3 acmap.py --uc UC-001     # every criterion of one use case
    python3 acmap.py --ac AC-001-08  # one criterion
    python3 acmap.py --all           # every criterion, tested or not
"""

import argparse
import ast
import re
import sys
from collections import defaultdict
from pathlib import Path

TAG = re.compile(r"@(AC-\d{3}-\d{2,})")
SCENARIO = re.compile(r"^\s*Scenario(?: Outline)?:")


def repo_root() -> Path:
    for path in [Path.cwd(), *Path.cwd().parents]:
        if (path / "docs" / "usecases").is_dir():
            return path
    sys.exit("acmap: run this from inside the JudgeLab repository")


def scenarios(root: Path) -> dict[str, dict]:
    """{criterion id: {file, line, retired, text}} in file order."""
    found = {}
    for feature in sorted((root / "docs" / "usecases").glob("UC-*/*.feature")):
        lines = feature.read_text(encoding="utf-8").splitlines()
        tags, current = [], None
        for number, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("@"):
                if current:
                    current = None
                tags.append(stripped)
            elif SCENARIO.match(line):
                ids = [i for tag in tags for i in TAG.findall(tag)]
                retired = any("@retired" in tag.split() for tag in tags)
                current = {"lines": [stripped]}
                for criterion in ids:
                    found[criterion] = {
                        "file": feature.relative_to(root),
                        "line": number,
                        "retired": retired,
                        "body": current["lines"],
                    }
                tags = []
            elif current is not None and stripped and not stripped.startswith("#"):
                current["lines"].append(stripped)
    return found


def marker_ids(decorator: ast.expr) -> list[str] | None:
    """The criterion IDs of an @pytest.mark.acceptance(...) decorator, else None."""
    if not isinstance(decorator, ast.Call):
        return None
    name = ast.unparse(decorator.func)
    if not name.endswith("mark.acceptance"):
        return None
    return [a.value for a in decorator.args if isinstance(a, ast.Constant)]


def case_count(decorators: list[ast.expr]) -> int:
    """How many runs the parametrize decorators produce (1 if none or unknown)."""
    total = 1
    for decorator in decorators:
        if (
            isinstance(decorator, ast.Call)
            and ast.unparse(decorator.func).endswith("mark.parametrize")
            and len(decorator.args) >= 2
            and isinstance(decorator.args[1], (ast.List, ast.Tuple))
        ):
            total *= len(decorator.args[1].elts)
    return total


def marked_tests(root: Path) -> dict[str, list[dict]]:
    """{criterion id: [{file, line, name, cases}]} for every marked test."""
    tests = defaultdict(list)
    for path in sorted((root / "tests").rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            ids = [i for d in node.decorator_list for i in (marker_ids(d) or [])]
            for criterion in ids:
                tests[criterion].append(
                    {
                        "file": path.relative_to(root),
                        "line": node.lineno,
                        "name": node.name,
                        "cases": case_count(node.decorator_list),
                    }
                )
    return tests


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--uc", help="only this use case, e.g. UC-001")
    scope.add_argument("--ac", help="only this criterion, e.g. AC-001-08")
    scope.add_argument("--all", action="store_true", help="include untested criteria")
    args = parser.parse_args()

    root = repo_root()
    defined = scenarios(root)
    tests = marked_tests(root)

    if args.ac:
        wanted = [args.ac]
    elif args.uc:
        prefix = "AC-" + args.uc.removeprefix("UC-") + "-"
        wanted = [c for c in defined if c.startswith(prefix)]
    elif args.all:
        wanted = list(defined)
    else:
        wanted = [c for c in defined if c in tests]

    for criterion in wanted:
        scenario = defined.get(criterion)
        print(f"## {criterion}")
        if scenario is None:
            print("NOT DEFINED in any feature file\n")
        else:
            state = " (RETIRED)" if scenario["retired"] else ""
            print(f"Defined{state}: {scenario['file']}:{scenario['line']}")
            print("```gherkin")
            print("\n".join(scenario["body"]))
            print("```")
        if tests.get(criterion):
            print("Marked tests:")
            for t in tests[criterion]:
                print(f"- {t['file']}:{t['line']} {t['name']} ({t['cases']} case(s))")
        else:
            print("Marked tests: none")
        print()

    undefined = sorted(set(tests) - set(defined))
    retired = sorted(c for c in tests if c in defined and defined[c]["retired"])
    if undefined or retired:
        print("## Marker problems")
        for criterion in undefined:
            print(f"- {criterion} is marked on a test but not defined in any feature file")
        for criterion in retired:
            print(f"- {criterion} is retired but still marked on a test")


if __name__ == "__main__":
    main()
