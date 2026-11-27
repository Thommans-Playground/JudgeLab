"""Render the PlantUML diagrams under docs/ to SVG, and check they are up to date.

Every `<name>.puml` is rendered to `<name>.svg` beside it. Each SVG records the
SHA-256 of the source it was rendered from (the .puml plus every file it
!includes), so `--check` can tell a stale SVG without running PlantUML.

    python3 render_diagrams.py            # render missing or stale SVGs
    python3 render_diagrams.py --all      # re-render everything
    python3 render_diagrams.py --check    # exit 1 if any SVG is missing or stale (no Java needed)

Rendering needs PlantUML: `plantuml` on PATH (e.g. `brew install plantuml`), or
the environment variable PLANTUML_JAR pointing at plantuml.jar (Java required).
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

INCLUDE = re.compile(r"^\s*!include\s+(\S+)", re.M)
STAMP = "judgelab-source-sha256"
STAMP_RE = re.compile(rf"<!-- {STAMP}: ([0-9a-f]{{64}}) -->")


def source_hash(puml: Path) -> str:
    """Hash the diagram and, recursively, the files it includes."""
    digest = hashlib.sha256()
    seen: set[Path] = set()

    def add(path: Path) -> None:
        path = path.resolve()
        if path in seen or not path.exists():
            return
        seen.add(path)
        text = path.read_text(encoding="utf-8")
        digest.update(text.encode("utf-8"))
        for target in INCLUDE.findall(text):
            add(path.parent / target)

    add(puml)
    return digest.hexdigest()


def recorded_hash(svg: Path) -> str | None:
    if not svg.exists():
        return None
    match = STAMP_RE.search(svg.read_text(encoding="utf-8", errors="replace"))
    return match.group(1) if match else None


def status(puml: Path) -> str:
    """'ok', 'missing' or 'stale'."""
    svg = puml.with_suffix(".svg")
    recorded = recorded_hash(svg)
    if recorded is None:
        return "missing" if not svg.exists() else "stale"
    return "ok" if recorded == source_hash(puml) else "stale"


def plantuml_command() -> list[str]:
    jar = os.environ.get("PLANTUML_JAR")
    if jar:
        return ["java", "-Djava.awt.headless=true", "-jar", jar]
    exe = shutil.which("plantuml")
    if exe:
        return [exe]
    sys.exit(
        "error: PlantUML not found. Install it (brew install plantuml) "
        "or set PLANTUML_JAR to the path of plantuml.jar."
    )


def render(puml: Path, command: list[str]) -> str | None:
    """Render one diagram. Returns an error message, or None on success."""
    # -pipe writes exactly one SVG to stdout; running in the file's folder makes
    # relative !include paths resolve the same way as in an editor preview.
    result = subprocess.run(
        [*command, "-tsvg", "-pipe", "-failfast2", "-charset", "UTF-8"],
        input=puml.read_bytes(),
        cwd=puml.parent,
        capture_output=True,
    )
    svg = result.stdout.decode("utf-8", errors="replace")
    if result.returncode != 0 or "<svg" not in svg:
        detail = result.stderr.decode("utf-8", errors="replace").strip() or svg[:300]
        return detail or f"exit code {result.returncode}"
    stamp = f"<!-- {STAMP}: {source_hash(puml)} -->"
    head, sep, rest = svg.partition("<svg")
    puml.with_suffix(".svg").write_text(f"{head}{stamp}\n{sep}{rest}", encoding="utf-8")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="only report missing or stale SVGs")
    mode.add_argument("--all", action="store_true", help="re-render every diagram")
    args = parser.parse_args()

    diagrams = sorted((args.root / "docs").rglob("*.puml"))
    states = {p: status(p) for p in diagrams}
    rel = lambda p: p.relative_to(args.root)  # noqa: E731

    if args.check:
        bad = {p: s for p, s in states.items() if s != "ok"}
        for path, state in bad.items():
            print(f"{state:8} {rel(path).with_suffix('.svg')}")
        print(f"{len(diagrams)} diagrams, {len(bad)} need rendering")
        return 1 if bad else 0

    todo = diagrams if args.all else [p for p, s in states.items() if s != "ok"]
    if not todo:
        print(f"{len(diagrams)} diagrams, all up to date")
        return 0
    command = plantuml_command()
    failures = 0
    for path in todo:
        error = render(path, command)
        if error:
            failures += 1
            print(f"FAILED   {rel(path)}\n  {error}")
        else:
            print(f"rendered {rel(path).with_suffix('.svg')}")
    print(f"{len(todo) - failures} rendered, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
