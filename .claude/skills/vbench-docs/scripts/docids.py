#!/usr/bin/env python3
"""Allocate document IDs and check documentation hygiene.

Usage:
  docids.py next KIND                       Print the next free ID (e.g. REQ-002)
  docids.py new KIND --title T [--release R] Create the item file from its template
  docids.py new concept --title TestCase    Create docs/ontology/test-case.md from docs/ontology/_template.md
  docids.py check [--strict]                Report ID, index, link and traceability problems
  docids.py list [KIND]                     List defined IDs and where they live

KIND is one of: REQ, UC, ADR, T, TC.  IDs look like REQ-001, UC-001, ADR-001, TC-001, T001.
Item files are named <ID>.md or <ID>-<slug>.md (e.g. T001-connection-profile.md).
Standard library only. Exit code 1 means errors were found (or warnings, with --strict).
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration: adjust here if a repo lays out docs/ differently.
# "dir" is relative to docs/; "index" is the README that must link every item.
# Tasks live under releases/<version>/tasks/ and are indexed by that release's README.
# Test cases (TC) are rows in verification.md rather than files.
# ---------------------------------------------------------------------------
KINDS = {
    "REQ": {"prefix": "REQ-", "dir": "requirements", "index": "requirements/README.md", "template": "req.md"},
    "UC": {"prefix": "UC-", "dir": "usecases", "index": "usecases/README.md", "template": "uc.md"},
    "ADR": {"prefix": "ADR-", "dir": "decisions", "index": "decisions/README.md", "template": "adr.md"},
    "T": {"prefix": "T", "dir": "releases/*/tasks", "index": None, "template": "task.md"},
    "TC": {"prefix": "TC-", "rows_in": "verification.md"},
}
ONTOLOGY = "ontology"  # concept files: <kebab-name>.md, each listed in ontology/README.md
TRACEABILITY = "traceability.md"
TRACED_KINDS = ("REQ", "T")  # every one of these should appear in traceability.md
WIDTH = 3

# Longest prefixes first so "TC-001" isn't read as kind "T".
_PREFIXES = sorted((c["prefix"] for c in KINDS.values()), key=len, reverse=True)
ID_RE = re.compile(r"\b(" + "|".join(map(re.escape, _PREFIXES)) + r")(\d{%d,})\b" % WIDTH)
KIND_OF_PREFIX = {c["prefix"]: k for k, c in KINDS.items()}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
TEMPLATES = Path(__file__).resolve().parent.parent / "assets" / "templates"


def kind_of(i: str) -> str:
    m = ID_RE.fullmatch(i)
    return KIND_OF_PREFIX[m.group(1)]


def num_of(i: str) -> int:
    return int(ID_RE.fullmatch(i).group(2))


def make_id(kind: str, n: int) -> str:
    return f"{KINDS[kind]['prefix']}{n:0{WIDTH}d}"


def repo_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True)
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def version_key(name: str):
    return [int(p) if p.isdigit() else p for p in re.split(r"[.\-]", name.lstrip("v"))]


class Docs:
    def __init__(self, root: Path):
        self.root = root
        self.docs = root / "docs"
        if not self.docs.is_dir():
            sys.exit(f"error: no docs/ directory under {root}")
        self.files = sorted(p for p in self.docs.rglob("*.md"))
        self.text = {p: p.read_text(encoding="utf-8") for p in self.files}
        self.defs: dict[str, list[Path]] = defaultdict(list)
        self._collect_definitions()

    def rel(self, p: Path) -> str:
        return str(p.relative_to(self.root))

    def _collect_definitions(self):
        for kind, cfg in KINDS.items():
            if "rows_in" in cfg:
                path = self.docs / cfg["rows_in"]
                if path.exists():
                    pat = re.compile(rf"^\|\s*\[?({re.escape(cfg['prefix'])}\d{{{WIDTH},}})\]?")
                    for line in self.text.get(path, "").splitlines():
                        m = pat.match(line)
                        if m:
                            self.defs[m.group(1)].append(path)
                continue
            pat = re.compile(rf"({re.escape(cfg['prefix'])}\d{{{WIDTH},}})(-[a-z0-9-]+)?")
            for path in self.docs.glob(f"{cfg['dir']}/*.md"):
                m = pat.fullmatch(path.stem)
                if m:
                    self.defs[m.group(1)].append(path)

    def mentions(self):
        """Yield (id, path, line_no) for every ID mentioned in docs/."""
        for path, text in self.text.items():
            for n, line in enumerate(text.splitlines(), 1):
                for m in ID_RE.finditer(line):
                    yield m.group(0), path, n

    def next_id(self, kind: str) -> str:
        # Consider both defined items and any mention, so retired/deleted IDs are never reused.
        nums = [num_of(i) for i in self.defs if kind_of(i) == kind]
        nums += [num_of(i) for i, _, _ in self.mentions() if kind_of(i) == kind]
        return make_id(kind, max(nums, default=0) + 1)

    def latest_release(self) -> str | None:
        rel = self.docs / "releases"
        names = [p.name for p in rel.iterdir() if p.is_dir()] if rel.is_dir() else []
        return max(names, key=version_key) if names else None


def cmd_next(d: Docs, a):
    print(d.next_id(a.kind))


def concept_files(d: Docs) -> list[Path]:
    folder = d.docs / ONTOLOGY
    return sorted(p for p in folder.glob("*.md")
                  if p.name != "README.md" and not p.name.startswith("_")) if folder.is_dir() else []


def new_concept(d: Docs, term: str):
    slug = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", term.strip()).replace(" ", "-").lower()
    target = d.docs / ONTOLOGY / f"{slug}.md"
    if target.exists():
        sys.exit(f"error: {d.rel(target)} already exists")
    template = d.docs / ONTOLOGY / "_template.md"
    target.write_text(template.read_text(encoding="utf-8").replace("<Concept>", term, 1), encoding="utf-8")
    print(f"Created {d.rel(target)}")
    print(f"Next: add {term} to the glossary in docs/{ONTOLOGY}/README.md")


def cmd_new(d: Docs, a):
    kind = a.kind
    if kind == "concept":
        return new_concept(d, a.title)
    new_id = d.next_id(kind)
    if kind == "TC":
        print(new_id)
        print(f"Add a row to docs/{KINDS['TC']['rows_in']}: | {new_id} | {a.title} | <level> | <REQ-###> |")
        return
    release = a.release or d.latest_release()
    if kind == "T":
        if not release:
            sys.exit("error: tasks need a release; create docs/releases/<version>/ or pass --release")
        target_dir = d.docs / "releases" / release / "tasks"
    else:
        target_dir = d.docs / KINDS[kind]["dir"]
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{new_id}.md"
    template = (TEMPLATES / KINDS[kind]["template"]).read_text(encoding="utf-8")
    body = (template.replace("{{ID}}", new_id)
                    .replace("{{TITLE}}", a.title)
                    .replace("{{RELEASE}}", release or "")
                    .replace("{{DATE}}", dt.date.today().isoformat()))
    target.write_text(body, encoding="utf-8")
    index = (f"docs/releases/{release}/README.md" if kind == "T"
             else f"docs/{KINDS[kind]['index']}")
    print(new_id)
    print(f"Created {d.rel(target)}")
    print(f"Next: list {new_id} in {index}" + (f" and add a row to docs/{TRACEABILITY}" if kind in TRACED_KINDS else ""))


def cmd_list(d: Docs, a):
    for i in sorted(d.defs, key=lambda x: (kind_of(x), num_of(x))):
        if a.kind and kind_of(i) != a.kind:
            continue
        print(f"{i:10} {', '.join(d.rel(p) for p in d.defs[i])}")


def cmd_check(d: Docs, a) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Duplicate IDs
    for i, paths in d.defs.items():
        if len(paths) > 1:
            errors.append(f"duplicate ID {i}: " + ", ".join(d.rel(p) for p in paths))

    # 2. File heading starts with the item's ID
    for i, paths in d.defs.items():
        for p in paths:
            if p.suffix != ".md" or not p.stem.startswith(i):
                continue
            first = next((l for l in d.text[p].splitlines() if l.startswith("# ")), "")
            if not first.startswith(f"# {i}"):
                errors.append(f"{d.rel(p)}: heading should start with '# {i}' (found {first!r})")

    # 3. Every item file is listed (linked or mentioned by ID) in its index
    for i, paths in d.defs.items():
        kind = kind_of(i)
        if "rows_in" in KINDS[kind]:
            continue
        for p in paths:
            index = (p.parent.parent / "README.md" if kind == "T"
                     else d.docs / KINDS[kind]["index"])
            if not index.exists():
                errors.append(f"{i}: index {d.rel(index)} is missing")
            elif not re.search(rf"\b{re.escape(i)}\b", d.text[index]):
                errors.append(f"{i}: not listed in {d.rel(index)}")

    # 4. Every mentioned ID is defined
    for i, p, n in d.mentions():
        if i not in d.defs:
            errors.append(f"{d.rel(p)}:{n}: {i} is referenced but not defined")

    # 5. Relative links resolve
    for p, text in d.text.items():
        for n, line in enumerate(text.splitlines(), 1):
            for target in LINK_RE.findall(line):
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    continue
                dest = (p.parent / target.split("#", 1)[0]).resolve()
                if not dest.exists():
                    errors.append(f"{d.rel(p)}:{n}: broken link {target}")

    # 6. Every ontology concept file is in the glossary
    glossary = d.text.get(d.docs / ONTOLOGY / "README.md", "")
    for p in concept_files(d):
        first = next((l[2:].strip() for l in d.text[p].splitlines() if l.startswith("# ")), "")
        if not first or first.startswith("<"):
            errors.append(f"{d.rel(p)}: missing a '# <Term>' heading")
        elif not re.search(rf"^\|\s*\[?`?{re.escape(first)}`?\]?", glossary, re.M):
            errors.append(f"{d.rel(p)}: term '{first}' is not in the glossary (docs/{ONTOLOGY}/README.md)")

    # 7. Traceability coverage (warnings)
    trace = d.docs / TRACEABILITY
    traced = {i for i, p, _ in d.mentions() if p == trace}
    for i in d.defs:
        if kind_of(i) in TRACED_KINDS and i not in traced:
            warnings.append(f"{i} is not in docs/{TRACEABILITY}")

    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    print(f"\n{len(d.defs)} IDs defined · {len(errors)} error(s) · {len(warnings)} warning(s)")
    return 1 if errors or (a.strict and warnings) else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="repository root (default: git top-level or cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("next"); p.add_argument("kind", choices=KINDS)
    p = sub.add_parser("new"); p.add_argument("kind", choices=[*KINDS, "concept"])
    p.add_argument("--title", required=True); p.add_argument("--release")
    p = sub.add_parser("list"); p.add_argument("kind", nargs="?", choices=KINDS)
    p = sub.add_parser("check"); p.add_argument("--strict", action="store_true",
                                                help="treat warnings as errors")
    a = ap.parse_args()
    d = Docs(repo_root(a.root))
    return {"next": cmd_next, "new": cmd_new, "list": cmd_list, "check": cmd_check}[a.cmd](d, a) or 0


if __name__ == "__main__":
    sys.exit(main())
