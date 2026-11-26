#!/usr/bin/env python3
"""Allocate document IDs and check documentation hygiene.

Usage:
  docids.py next KIND                       Print the next free ID (e.g. REQ-002)
  docids.py new KIND --title T [--release R] Create the item file from its template
  docids.py new concept --title TestCase    Create docs/ontology/test-case.md from docs/ontology/_template.md
  docids.py new context --title Evaluation  Create docs/domain/evaluation/README.md (a DDD bounded context)
  docids.py new model --context evaluation --title JudgeEvaluation   Aggregate/entity/value object/service
  docids.py new event --context evaluation --title EvaluationCompleted   Domain event
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
DOMAIN = "domain"      # DDD: domain/<context>/README.md + one file per model/event
DDD_TYPES = {"Aggregate Root", "Entity", "Value Object", "Domain Service", "Domain Event"}
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
    target = d.docs / ONTOLOGY / f"{slugify(term)}.md"
    if target.exists():
        sys.exit(f"error: {d.rel(target)} already exists")
    template = d.docs / ONTOLOGY / "_template.md"
    target.write_text(template.read_text(encoding="utf-8").replace("<Concept>", term, 1), encoding="utf-8")
    print(f"Created {d.rel(target)}")
    print(f"Next: add {term} to the glossary in docs/{ONTOLOGY}/README.md")


def slugify(term: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", term.strip()).replace(" ", "-").lower()


def field(text: str, name: str) -> str:
    """Value of a '| Name | Value |' metadata row, with links/backticks stripped; '' if unset."""
    m = re.search(rf"^\|\s*{re.escape(name)}\s*\|\s*(.*?)\s*\|\s*$", text, re.M)
    v = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", m.group(1)).strip("` ") if m else ""
    return "" if not v or v.startswith("<") or v in {"—", "-"} else v


def heading(text: str) -> str:
    return next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), "")


def table_terms(text: str) -> set[str]:
    """First-column terms of every Markdown table row (links/backticks stripped)."""
    out = set()
    for line in text.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|", line)
        if m:
            out.add(re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", m.group(1)).strip("` "))
    return out


def context_dirs(d: Docs) -> list[Path]:
    root = d.docs / DOMAIN
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def domain_files(ctx: Path) -> list[Path]:
    return sorted(p for p in ctx.glob("*.md") if p.name != "README.md" and not p.name.startswith("_"))


def new_domain(d: Docs, a):
    release = a.release or d.latest_release() or ""
    if a.kind == "context":
        target = d.docs / DOMAIN / slugify(a.title) / "README.md"
        template, context_title, index = "domain-context.md", a.title, f"docs/{DOMAIN}/README.md (bounded contexts table and context map)"
    else:
        if not a.context:
            sys.exit(f"error: --context is required for {a.kind}; existing: "
                     + (", ".join(p.name for p in context_dirs(d)) or "none (run `new context` first)"))
        ctx = d.docs / DOMAIN / a.context
        if not (ctx / "README.md").exists():
            sys.exit(f"error: no bounded context at {d.rel(ctx)}; run `new context` first")
        target = ctx / f"{slugify(a.title)}.md"
        template = "domain-event.md" if a.kind == "event" else "domain-model.md"
        context_title, index = heading(d.text[ctx / "README.md"]), f"the ubiquitous language table in {d.rel(ctx / 'README.md')}"
    if target.exists():
        sys.exit(f"error: {d.rel(target)} already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    body = ((TEMPLATES / template).read_text(encoding="utf-8")
            .replace("{{TITLE}}", a.title).replace("{{CONTEXT}}", context_title).replace("{{RELEASE}}", release))
    target.write_text(body, encoding="utf-8")
    print(f"Created {d.rel(target)}")
    print(f"Next: add {a.title} to {index}")


def cmd_new(d: Docs, a):
    kind = a.kind
    if kind == "concept":
        return new_concept(d, a.title)
    if kind in ("context", "model", "event"):
        return new_domain(d, a)
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

    # 7. DDD domain model
    ontology_terms = table_terms(glossary) | {heading(d.text[p]) for p in concept_files(d)}
    domain_index = d.text.get(d.docs / DOMAIN / "README.md", "")
    for ctx in context_dirs(d):
        readme = ctx / "README.md"
        if readme not in d.text:
            errors.append(f"{d.rel(ctx)}/: bounded context has no README.md")
            continue
        ctx_title = heading(d.text[readme])
        if ctx_title not in table_terms(domain_index):
            errors.append(f"{d.rel(readme)}: context '{ctx_title}' is not in the bounded contexts table "
                          f"(docs/{DOMAIN}/README.md)")
        language = table_terms(d.text[readme])
        models = {heading(d.text[p]): d.text[p] for p in domain_files(ctx)}
        for p in domain_files(ctx):
            text, term = d.text[p], heading(d.text[p])
            where = d.rel(p)
            if not term or term.startswith("<"):
                errors.append(f"{where}: missing a '# <Name>' heading"); continue
            if term not in language:
                errors.append(f"{where}: '{term}' is not in the ubiquitous language table of {d.rel(readme)}")
            ddd = field(text, "DDD Type")
            if ddd and ddd not in DDD_TYPES:
                errors.append(f"{where}: DDD Type '{ddd}' is not one of {', '.join(sorted(DDD_TYPES))}")
            bc = field(text, "Bounded Context")
            if bc and bc != ctx_title:
                errors.append(f"{where}: Bounded Context '{bc}' doesn't match its folder's context '{ctx_title}'")
            if ddd == "Entity":
                owner = field(text, "Aggregate")
                if not owner:
                    errors.append(f"{where}: Entity must name its owning Aggregate Root")
                elif field(models.get(owner, ""), "DDD Type") != "Aggregate Root":
                    errors.append(f"{where}: Aggregate '{owner}' is not an Aggregate Root in context '{ctx_title}'")
            onto = field(text, "Ontology")
            if onto and onto not in ontology_terms:
                errors.append(f"{where}: Ontology concept '{onto}' is not defined in docs/{ONTOLOGY}/")

    # 8. Traceability coverage (warnings)
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
    p = sub.add_parser("new"); p.add_argument("kind", choices=[*KINDS, "concept", "context", "model", "event"])
    p.add_argument("--title", required=True); p.add_argument("--release")
    p.add_argument("--context", help="bounded context folder (for model/event)")
    p = sub.add_parser("list"); p.add_argument("kind", nargs="?", choices=KINDS)
    p = sub.add_parser("check"); p.add_argument("--strict", action="store_true",
                                                help="treat warnings as errors")
    a = ap.parse_args()
    d = Docs(repo_root(a.root))
    return {"next": cmd_next, "new": cmd_new, "list": cmd_list, "check": cmd_check}[a.cmd](d, a) or 0


if __name__ == "__main__":
    sys.exit(main())
