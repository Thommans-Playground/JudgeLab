#!/usr/bin/env python3
"""Allocate document IDs and check documentation hygiene.

Usage:
  docids.py next KIND                       Print the next free ID (e.g. REQ-002)
  docids.py new KIND --title T [--release R] Create the item file from its template
  docids.py new UC --title "Prepare dataset" Create docs/usecases/UC-00N-prepare-dataset/README.md
  docids.py new T --usecase UC-002 --title "JSON loader"   Create a task (slice) in that use case
  docids.py next AC --usecase UC-004        Print the next acceptance-criterion ID (AC-004-06)
  docids.py next T --usecase UC-004         Print the next task ID in that use case (T-004-03)
  docids.py new concept --title TestCase    Create docs/ontology/test-case.md (from _template.md)
  docids.py new context --title Evaluation  Create docs/domain/evaluation/README.md (a context)
  docids.py new model --context evaluation --title JudgeEvaluation   Aggregate/entity/VO/service
  docids.py new event --context evaluation --title EvaluationCompleted   Domain event
  docids.py check [--strict]                Report ID, index, link and traceability problems
  docids.py list [KIND]                     List defined IDs and where they live

KIND is one of: REQ, UC, ADR, T, TC.  IDs look like REQ-001, UC-001, ADR-001, TC-001, and
T-001-03 (task 03 of UC-001). Item files are named <ID>.md or <ID>-<slug>.md
(e.g. T-001-03-openai-connector.md).
Use cases are folders (usecases/UC-001-<slug>/README.md) that also hold their tasks, the
use case's slices. Acceptance criteria (AC-001-01) are defined in the use case README.
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
# Use cases are folders: usecases/UC-###-<slug>/README.md. Tasks (T-UUU-NN) are slices of
# use case UC-UUU and live inside its folder, indexed by the use case README.
# Test cases (TC) are rows in verification.md rather than files.
# ---------------------------------------------------------------------------
KINDS = {
    "REQ": {
        "prefix": "REQ-",
        "dir": "requirements",
        "index": "requirements/README.md",
        "template": "req.md",
    },
    "UC": {
        "prefix": "UC-",
        "dir": "usecases",
        "folder": True,
        "index": "usecases/README.md",
        "template": "uc.md",
    },
    "ADR": {
        "prefix": "ADR-",
        "dir": "decisions",
        "index": "decisions/README.md",
        "template": "adr.md",
    },
    "T": {
        "prefix": "T-",
        "scoped": True,
        "dir": "usecases/*",
        "index": None,
        "template": "task.md",
    },
    "TC": {"prefix": "TC-", "rows_in": "verification.md"},
}
ONTOLOGY = "ontology"  # concept files: <kebab-name>.md, each listed in ontology/README.md
DOMAIN = "domain"  # DDD: domain/<context>/README.md + one file per model/event
DDD_TYPES = {"Aggregate Root", "Entity", "Value Object", "Domain Service", "Domain Event"}
TRACEABILITY = "traceability.md"
TRACED_KINDS = ("REQ", "T")  # every one of these should appear in traceability.md
WIDTH = 3

# Plain IDs are PREFIX + number (REQ-001). Scoped IDs (tasks) carry their use case: T-004-02.
_PLAIN = [c["prefix"] for c in KINDS.values() if not c.get("scoped")]
_SCOPED = [c["prefix"] for c in KINDS.values() if c.get("scoped")]
ID_RE = re.compile(
    r"\b(?:(" + "|".join(map(re.escape, _PLAIN)) + rf")(\d{{{WIDTH},}})"
    r"|(" + "|".join(map(re.escape, _SCOPED)) + rf")(\d{{{WIDTH}}})-(\d{{2,}}))\b"
)
KIND_OF_PREFIX = {c["prefix"]: k for k, c in KINDS.items()}
AC_RE = re.compile(rf"\bAC-(\d{{{WIDTH}}})-(\d{{2,}})\b")  # AC-004-01: criterion 01 of UC-004
AC_DEFINITION = re.compile(rf"\*\*(AC-\d{{{WIDTH}}}-\d{{2,}})\*\*")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
TEMPLATES = Path(__file__).resolve().parent.parent / "assets" / "templates"


def kind_of(i: str) -> str:
    m = ID_RE.fullmatch(i)
    return KIND_OF_PREFIX[m.group(1) or m.group(3)]


def num_of(i: str) -> int:
    m = ID_RE.fullmatch(i)
    return int(m.group(2) or m.group(5))


def scope_of(i: str) -> str | None:
    """The use case number a scoped ID belongs to: T-004-02 -> '004'."""
    return ID_RE.fullmatch(i).group(4)


def sort_key(i: str) -> tuple:
    return (kind_of(i), scope_of(i) or "", num_of(i))


def make_id(kind: str, n: int, scope: str | None = None) -> str:
    if KINDS[kind].get("scoped"):
        return f"{KINDS[kind]['prefix']}{scope}-{n:02d}"
    return f"{KINDS[kind]['prefix']}{n:0{WIDTH}d}"


def repo_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
        )
        return Path(out.stdout.strip())
    except subprocess.CalledProcessError, FileNotFoundError:
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
        for cfg in KINDS.values():
            if "rows_in" in cfg:
                path = self.docs / cfg["rows_in"]
                if path.exists():
                    pat = re.compile(rf"^\|\s*\[?({re.escape(cfg['prefix'])}\d{{{WIDTH},}})\]?")
                    for line in self.text.get(path, "").splitlines():
                        m = pat.match(line)
                        if m:
                            self.defs[m.group(1)].append(path)
                continue
            number = rf"\d{{{WIDTH}}}-\d{{2,}}" if cfg.get("scoped") else rf"\d{{{WIDTH},}}"
            pat = re.compile(rf"({re.escape(cfg['prefix'])}{number})(-[a-z0-9-]+)?")
            if cfg.get("folder"):
                for path in self.docs.glob(f"{cfg['dir']}/*/README.md"):
                    m = pat.fullmatch(path.parent.name)
                    if m:
                        self.defs[m.group(1)].append(path)
                continue
            for path in self.docs.glob(f"{cfg['dir']}/*.md"):
                m = pat.fullmatch(path.stem)
                if m:
                    self.defs[m.group(1)].append(path)

    def usecase_dir(self, uc_id: str) -> Path:
        paths = self.defs.get(uc_id)
        if not paths:
            sys.exit(f"error: no use case {uc_id}; create it with `new UC --title ...`")
        return paths[0].parent

    def criteria(self) -> dict[str, list[Path]]:
        """Acceptance criteria defined (as **AC-###-##**) in use case READMEs."""
        found: dict[str, list[Path]] = defaultdict(list)
        for paths in (self.defs[i] for i in self.defs if kind_of(i) == "UC"):
            for path in paths:
                for m in AC_DEFINITION.finditer(self.text[path]):
                    found[m.group(1)].append(path)
        return found

    def mentions(self):
        """Yield (id, path, line_no) for every ID mentioned in docs/."""
        for path, text in self.text.items():
            for n, line in enumerate(text.splitlines(), 1):
                for m in ID_RE.finditer(line):
                    yield m.group(0), path, n

    def next_id(self, kind: str, usecase: str | None = None) -> str:
        # Consider both defined items and any mention, so retired/deleted IDs are never reused.
        scope = None
        if KINDS[kind].get("scoped"):
            if not usecase:
                sys.exit(f"error: {kind} IDs belong to a use case: pass --usecase UC-###")
            scope = usecase.removeprefix("UC-")
        ids = list(self.defs) + [i for i, _, _ in self.mentions()]
        nums = [num_of(i) for i in ids if kind_of(i) == kind and scope_of(i) == scope]
        return make_id(kind, max(nums, default=0) + 1, scope)

    def latest_release(self) -> str | None:
        rel = self.docs / "releases"
        names = [p.name for p in rel.iterdir() if p.is_dir()] if rel.is_dir() else []
        return max(names, key=version_key) if names else None


def cmd_next(d: Docs, a):
    if a.kind == "AC":
        if not a.usecase:
            sys.exit("error: next AC needs --usecase UC-###")
        number = a.usecase.removeprefix("UC-")
        used = [
            int(m.group(2))
            for p in d.files
            for m in AC_RE.finditer(d.text[p])
            if m.group(1) == number
        ]
        print(f"AC-{number}-{max(used, default=0) + 1:02d}")
        return
    print(d.next_id(a.kind, a.usecase))


def concept_files(d: Docs) -> list[Path]:
    folder = d.docs / ONTOLOGY
    return (
        sorted(
            p for p in folder.glob("*.md") if p.name != "README.md" and not p.name.startswith("_")
        )
        if folder.is_dir()
        else []
    )


def new_concept(d: Docs, term: str):
    target = d.docs / ONTOLOGY / f"{slugify(term)}.md"
    if target.exists():
        sys.exit(f"error: {d.rel(target)} already exists")
    template = d.docs / ONTOLOGY / "_template.md"
    target.write_text(
        template.read_text(encoding="utf-8").replace("<Concept>", term, 1), encoding="utf-8"
    )
    print(f"Created {d.rel(target)}")
    print(f"Next: add {term} to the glossary in docs/{ONTOLOGY}/README.md")


def slugify(term: str) -> str:
    """'TestCase' -> 'test-case', 'Anthropic (Claude) connector' -> 'anthropic-claude-connector'."""
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", term.strip())
    return re.sub(r"[^a-z0-9]+", "-", spaced.lower()).strip("-")


def field(text: str, name: str) -> str:
    """Value of a '| Name | Value |' metadata row, with links/backticks stripped; '' if unset."""
    m = re.search(rf"^\|\s*{re.escape(name)}\s*\|\s*(.*?)\s*\|\s*$", text, re.M)
    v = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", m.group(1)).strip("` ") if m else ""
    return "" if not v or v.startswith("<") or v in {"—", "-"} else v


def heading(text: str) -> str:
    return next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), "")


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
    return sorted(
        p for p in ctx.glob("*.md") if p.name != "README.md" and not p.name.startswith("_")
    )


def new_domain(d: Docs, a):
    release = a.release or d.latest_release() or ""
    if a.kind == "context":
        target = d.docs / DOMAIN / slugify(a.title) / "README.md"
        template, context_title, index = (
            "domain-context.md",
            a.title,
            f"docs/{DOMAIN}/README.md (bounded contexts table and context map)",
        )
    else:
        if not a.context:
            sys.exit(
                f"error: --context is required for {a.kind}; existing: "
                + (", ".join(p.name for p in context_dirs(d)) or "none (run `new context` first)")
            )
        ctx = d.docs / DOMAIN / a.context
        if not (ctx / "README.md").exists():
            sys.exit(f"error: no bounded context at {d.rel(ctx)}; run `new context` first")
        target = ctx / f"{slugify(a.title)}.md"
        template = "domain-event.md" if a.kind == "event" else "domain-model.md"
        context_title, index = (
            heading(d.text[ctx / "README.md"]),
            f"the ubiquitous language table in {d.rel(ctx / 'README.md')}",
        )
    if target.exists():
        sys.exit(f"error: {d.rel(target)} already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    body = (
        (TEMPLATES / template)
        .read_text(encoding="utf-8")
        .replace("{{TITLE}}", a.title)
        .replace("{{CONTEXT}}", context_title)
        .replace("{{RELEASE}}", release)
    )
    target.write_text(body, encoding="utf-8")
    print(f"Created {d.rel(target)}")
    print(f"Next: add {a.title} to {index}")


def cmd_new(d: Docs, a):
    kind = a.kind
    if kind == "concept":
        return new_concept(d, a.title)
    if kind in ("context", "model", "event"):
        return new_domain(d, a)
    new_id = d.next_id(kind, getattr(a, "usecase", None))
    if kind == "TC":
        print(new_id)
        print(
            f"Add a row to docs/{KINDS['TC']['rows_in']}: "
            f"| {new_id} | {a.title} | <level> | <REQ-###> |"
        )
        return
    release = a.release or d.latest_release()
    usecase = None
    if kind == "T":
        if not a.usecase:
            sys.exit("error: a task is a slice of a use case: pass --usecase UC-###")
        usecase = a.usecase
        target = d.usecase_dir(usecase) / f"{new_id}-{slugify(a.title)}.md"
    elif kind == "UC":
        target = d.docs / KINDS[kind]["dir"] / f"{new_id}-{slugify(a.title)}" / "README.md"
    else:
        target = d.docs / KINDS[kind]["dir"] / f"{new_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    template = (TEMPLATES / KINDS[kind]["template"]).read_text(encoding="utf-8")
    body = (
        template.replace("{{ID}}", new_id)
        .replace("{{TITLE}}", a.title)
        .replace("{{RELEASE}}", release or "")
        .replace("{{DATE}}", dt.date.today().isoformat())
        .replace("{{USECASE}}", usecase or "")
        .replace("{{NUM}}", new_id.removeprefix("UC-"))
    )
    target.write_text(body, encoding="utf-8")
    index = (
        f"the Slices table of {d.rel(target.parent / 'README.md')} and the release plan"
        if kind == "T"
        else f"docs/{KINDS[kind]['index']}"
    )
    print(new_id)
    print(f"Created {d.rel(target)}")
    print(
        f"Next: list {new_id} in {index}"
        + (f" and add a row to docs/{TRACEABILITY}" if kind in TRACED_KINDS else "")
    )


def cmd_list(d: Docs, a):
    for i in sorted(d.defs, key=sort_key):
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
            name = p.parent.name if p.name == "README.md" else p.stem
            if p.suffix != ".md" or not name.startswith(i):
                continue
            first = next((line for line in d.text[p].splitlines() if line.startswith("# ")), "")
            if not first.startswith(f"# {i}"):
                errors.append(f"{d.rel(p)}: heading should start with '# {i}' (found {first!r})")

    # 3. Every item file is listed (linked or mentioned by ID) in its index
    for i, paths in d.defs.items():
        kind = kind_of(i)
        if "rows_in" in KINDS[kind]:
            continue
        for p in paths:
            index = p.parent / "README.md" if kind == "T" else d.docs / KINDS[kind]["index"]
            if not index.exists():
                errors.append(f"{i}: index {d.rel(index)} is missing")
            elif not re.search(rf"\b{re.escape(i)}\b", d.text[index]):
                errors.append(f"{i}: not listed in {d.rel(index)}")

    # 4. Every mentioned ID is defined
    for i, p, n in d.mentions():
        if i not in d.defs:
            errors.append(f"{d.rel(p)}:{n}: {i} is referenced but not defined")

    # 4a. A task lives in the folder of the use case its ID names (T-004-02 in UC-004-...)
    for i, paths in d.defs.items():
        if kind_of(i) == "T":
            for p in paths:
                if not p.parent.name.startswith(f"UC-{scope_of(i)}"):
                    errors.append(f"{d.rel(p)}: {i} belongs in UC-{scope_of(i)}, not this use case")

    # 4b. Acceptance criteria: defined once, in their own use case, and every mention resolves
    criteria = d.criteria()
    for ac, paths in criteria.items():
        if len(paths) > 1:
            errors.append(f"duplicate criterion {ac}: " + ", ".join(d.rel(p) for p in paths))
        owner = f"UC-{ac.split('-')[1]}"
        for path in paths:
            if not path.parent.name.startswith(owner):
                errors.append(f"{d.rel(path)}: {ac} belongs in {owner}, not this use case")
    for path, text in d.text.items():
        for n, line in enumerate(text.splitlines(), 1):
            for m in AC_RE.finditer(line):
                if m.group(0) not in criteria:
                    errors.append(f"{d.rel(path)}:{n}: {m.group(0)} is referenced but not defined")

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
        first = next(
            (line[2:].strip() for line in d.text[p].splitlines() if line.startswith("# ")), ""
        )
        if not first or first.startswith("<"):
            errors.append(f"{d.rel(p)}: missing a '# <Term>' heading")
        elif not re.search(rf"^\|\s*\[?`?{re.escape(first)}`?\]?", glossary, re.M):
            errors.append(
                f"{d.rel(p)}: term '{first}' is not in the glossary (docs/{ONTOLOGY}/README.md)"
            )

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
            errors.append(
                f"{d.rel(readme)}: context '{ctx_title}' is not in the bounded contexts table "
                f"(docs/{DOMAIN}/README.md)"
            )
        language = table_terms(d.text[readme])
        models = {heading(d.text[p]): d.text[p] for p in domain_files(ctx)}
        for p in domain_files(ctx):
            text, term = d.text[p], heading(d.text[p])
            where = d.rel(p)
            if not term or term.startswith("<"):
                errors.append(f"{where}: missing a '# <Name>' heading")
                continue
            if term not in language:
                errors.append(
                    f"{where}: '{term}' is not in the ubiquitous language table of {d.rel(readme)}"
                )
            ddd = field(text, "DDD Type")
            if ddd and ddd not in DDD_TYPES:
                errors.append(
                    f"{where}: DDD Type '{ddd}' is not one of {', '.join(sorted(DDD_TYPES))}"
                )
            bc = field(text, "Bounded Context")
            if bc and bc != ctx_title:
                errors.append(
                    f"{where}: Bounded Context '{bc}' doesn't match "
                    f"its folder's context '{ctx_title}'"
                )
            if ddd == "Entity":
                owner = field(text, "Aggregate")
                if not owner:
                    errors.append(f"{where}: Entity must name its owning Aggregate Root")
                elif field(models.get(owner, ""), "DDD Type") != "Aggregate Root":
                    errors.append(
                        f"{where}: Aggregate '{owner}' is not an Aggregate Root "
                        f"in context '{ctx_title}'"
                    )
            onto = field(text, "Ontology")
            if onto and onto not in ontology_terms:
                errors.append(
                    f"{where}: Ontology concept '{onto}' is not defined in docs/{ONTOLOGY}/"
                )

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
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", help="repository root (default: git top-level or cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("next")
    p.add_argument("kind", choices=[*KINDS, "AC"])
    p.add_argument("--usecase", help="use case for an AC, e.g. UC-004")
    p = sub.add_parser("new")
    p.add_argument("kind", choices=[*KINDS, "concept", "context", "model", "event"])
    p.add_argument("--title", required=True)
    p.add_argument("--release")
    p.add_argument("--usecase", help="the use case a task belongs to (for new T)")
    p.add_argument("--context", help="bounded context folder (for model/event)")
    p = sub.add_parser("list")
    p.add_argument("kind", nargs="?", choices=KINDS)
    p = sub.add_parser("check")
    p.add_argument("--strict", action="store_true", help="treat warnings as errors")
    a = ap.parse_args()
    d = Docs(repo_root(a.root))
    return {"next": cmd_next, "new": cmd_new, "list": cmd_list, "check": cmd_check}[a.cmd](
        d, a
    ) or 0


if __name__ == "__main__":
    sys.exit(main())
