#!/usr/bin/env python3
"""Check that the code's imports follow the architecture in docs/design.md.

The rules are read from the "## Components" table of docs/design.md, so they
are written down once. For each component (a top-level module or package
under src/judgelab/), its "Depends on" cell lists what it may import:

    everything ...              any judgelab component (the composition root)
    `x`                         anything from component x
    `x` (port only)             only the port of x: its ModelConnector, ModelResponse
                                and *Error names, from its package front door
    `x.Name`                    only that name from component x
    provider SDKs (adapters only)
                                the component may import SDKs, but only in its
                                adapter modules (*_connector.py)
    —                           no other judgelab component

Plus the ADR-001 rules for the core: SDKs and HTTP clients (openai, anthropic,
httpx) only in adapter modules; YAML only in config.

    python3 archcheck.py            # report violations; exit 1 if any
    python3 archcheck.py --root DIR # check another checkout

Standard library only.
"""

import argparse
import ast
import re
import sys
from pathlib import Path

SDKS = {"openai", "anthropic", "httpx", "httpx2"}
YAML = {"yaml", "ruamel"}
PORT_NAMES = {"ModelConnector", "ModelResponse"}
ROW = re.compile(r"^\|\s*`([a-z_]+)`\s*\|[^|]*\|\s*(.*?)\s*\|\s*$")
TICK = re.compile(r"`([a-z_]+)(?:\.([A-Za-z_]+))?`(\s*\(port only\))?")


def repo_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "docs" / "design.md").is_file():
            return path
    sys.exit("archcheck: no docs/design.md found; run inside the repository")


def components(design: Path) -> dict[str, dict]:
    """{component: {"any": bool, "sdk": bool, "deps": {component: rule}}} from the table.

    A rule is None (anything), "port", or a set of allowed names.
    """
    table, inside = {}, False
    for line in design.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Components"
            continue
        match = ROW.match(line) if inside else None
        if not match:
            continue
        name, cell = match.groups()
        rules: dict = {}
        for dep, attr, port in TICK.findall(cell):
            if port:
                rules[dep] = "port"
            elif attr:
                current = rules.get(dep, set())
                if isinstance(current, set):
                    rules[dep] = current | {attr}
            else:
                rules[dep] = None
        table[name] = {
            "any": cell.lower().startswith("everything"),
            "sdk": "sdk" in cell.lower(),
            "deps": rules,
        }
    return table


def imports(path: Path):
    """Yield (line, module, names) for every import in a file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name, []
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.lineno, node.module, [a.name for a in node.names]


def is_port_import(module: str, names: list[str], component: str) -> bool:
    """Port only: from the package front door (or its errors/response modules), port names."""
    front_doors = {
        f"judgelab.{component}",
        f"judgelab.{component}.errors",
        f"judgelab.{component}.response",
        f"judgelab.{component}.port",
    }
    if module not in front_doors:
        return False
    return all(n in PORT_NAMES or n.endswith("Error") for n in names)


def check(root: Path) -> list[str]:
    table = components(root / "docs" / "design.md")
    package = root / "src" / "judgelab"
    problems = []
    for path in sorted(package.rglob("*.py")):
        relative = path.relative_to(package)
        if relative.parts[0] == "__init__.py":
            continue
        component = relative.parts[0].removesuffix(".py")
        where = path.relative_to(root)
        if component not in table:
            problems.append(f"{where}: component '{component}' is not in design.md's Components")
            continue
        rule = table[component]
        is_adapter = path.name.endswith("_connector.py")
        for line, module, names in imports(path):
            top = module.split(".")[0]
            if top in SDKS and not (rule["sdk"] and is_adapter):
                problems.append(
                    f"{where}:{line}: imports {module}; SDKs belong in adapter modules only"
                )
            if top in YAML and component != "config":
                problems.append(f"{where}:{line}: imports {module}; YAML belongs in config only")
            if top != "judgelab" or rule["any"]:
                continue
            parts = module.split(".")
            if len(parts) < 2:
                continue
            target = parts[1]
            if target == component:
                continue
            if target not in rule["deps"]:
                problems.append(
                    f"{where}:{line}: {component} imports {module}; "
                    f"design.md doesn't list {target} as a dependency of {component}"
                )
                continue
            allowed = rule["deps"][target]
            if allowed == "port" and not is_port_import(module, names, target):
                problems.append(
                    f"{where}:{line}: {component} imports {module} ({', '.join(names)}); "
                    f"only the {target} port is allowed"
                )
            elif isinstance(allowed, set) and not set(names) <= allowed:
                extra = ", ".join(sorted(set(names) - allowed))
                problems.append(
                    f"{where}:{line}: {component} imports {extra} from {target}; "
                    f"only {', '.join(sorted(allowed))} is allowed"
                )
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = repo_root(args.root.resolve())
    problems = check(root)
    for problem in problems:
        print(problem)
    print(f"archcheck: {len(problems)} violation(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
