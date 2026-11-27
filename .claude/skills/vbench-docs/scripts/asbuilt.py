#!/usr/bin/env python3
"""Draw "as-built" PlantUML diagrams from the real code, to compare against the design diagrams.

Usage (run from the project root, inside its environment):
  uv run python asbuilt.py sequence <pytest node id> [-o out.puml] [--package judgelab]
                                    [--include-private] [--max-depth N] [--title T]
  uv run python asbuilt.py classes <module> [<module> ...] [-o out.puml] [--package judgelab]

`sequence` runs one test and records the package's function calls during its call phase
(sys.monitoring), drawing argument *names* and return *types* only, never values.
Exit status is 1 if the test failed (the diagram is still written, with a note).
`classes` imports the modules and draws the classes and public functions defined in them.
Standard library only, plus pytest for `sequence`.
"""

from __future__ import annotations

import annotationlib
import argparse
import contextlib
import dataclasses
import enum
import importlib
import inspect
import re
import sys
from dataclasses import dataclass, field
from types import CodeType, FrameType
from typing import Any

MON = sys.monitoring
TOOL_ID = MON.PROFILER_ID
EVENTS = MON.events
MAX_PERIOD = 4  # longest repeating group of sibling calls folded into one `loop`


RESERVED = {"end", "loop", "alt", "else", "group", "note", "box", "ref", "par", "opt", "break"}


def alias(name: str) -> str:
    """A PlantUML-safe identifier for a participant or class name."""
    safe = re.sub(r"\W", "_", name)
    return f"{safe}_" if safe.lower() in RESERVED else safe


def type_name(value: object) -> str:
    return "None" if value is None else type(value).__name__


# --------------------------------------------------------------------------- sequence


@dataclass
class Call:
    participant: str
    label: str
    hidden: bool = False
    creates: bool = False  # an __init__: drawn as `create`, with no return arrow
    result: str = ""
    children: list[Call] = field(default_factory=list)


class Recorder:
    """Builds a call tree of the package's Python functions while it is started."""

    def __init__(self, package: str, include_private: bool) -> None:
        self.package, self.include_private = package, include_private
        self.root = Call("Test", "")
        self.stack: list[tuple[CodeType, Call]] = []
        self.ours: dict[CodeType, bool] = {}

    def callbacks(self) -> dict[int, Any]:
        return {
            EVENTS.PY_START: self.on_start,
            EVENTS.PY_RETURN: self.on_return,
            EVENTS.PY_YIELD: self.on_yield,
            EVENTS.PY_UNWIND: self.on_unwind,
        }

    def start(self) -> None:
        MON.use_tool_id(TOOL_ID, "asbuilt")
        for event, callback in self.callbacks().items():
            MON.register_callback(TOOL_ID, event, callback)
        MON.set_events(TOOL_ID, sum(self.callbacks()))  # the event flags are distinct bits

    def stop(self) -> None:
        MON.set_events(TOOL_ID, 0)
        for event in self.callbacks():
            MON.register_callback(TOOL_ID, event, None)
        MON.free_tool_id(TOOL_ID)

    def is_ours(self, code: CodeType, frame: FrameType) -> bool:
        if code not in self.ours:
            module = frame.f_globals.get("__name__", "")
            self.ours[code] = module == self.package or module.startswith(self.package + ".")
        return self.ours[code]

    def on_start(self, code: CodeType, offset: int) -> Any:
        frame = sys._getframe(1)
        if not self.is_ours(code, frame):
            return MON.DISABLE  # never ask again for this code: keeps the test fast
        node = self.describe(code, frame)
        parent = self.stack[-1][1] if self.stack else self.root
        parent.children.append(node)
        self.stack.append((code, node))

    def on_return(self, code: CodeType, offset: int, value: object) -> Any:
        if not self.is_ours(code, sys._getframe(1)):
            return MON.DISABLE
        self.finish(code, type_name(value))

    def on_yield(self, code: CodeType, offset: int, value: object) -> Any:
        if not self.is_ours(code, sys._getframe(1)):
            return MON.DISABLE
        self.finish(code, f"yield {type_name(value)}")  # later resumes are not drawn

    def on_unwind(self, code: CodeType, offset: int, exc: BaseException) -> None:
        if self.is_ours(code, sys._getframe(1)):  # PY_UNWIND cannot be disabled
            self.finish(code, f"raise {type(exc).__name__}")

    def finish(self, code: CodeType, result: str) -> None:
        if self.stack and self.stack[-1][0] is code:
            self.stack.pop()[1].result = result

    def describe(self, code: CodeType, frame: FrameType) -> Call:
        """Who receives this call and how to label it. Reads only `self`/`cls`, never values."""
        nargs = code.co_argcount + code.co_kwonlyargcount
        nargs += bool(code.co_flags & inspect.CO_VARARGS)
        nargs += bool(code.co_flags & inspect.CO_VARKEYWORDS)
        args = list(code.co_varnames[:nargs])
        name, qualname = code.co_name, code.co_qualname
        owner: type | None = None
        if code.co_argcount and args[0] in ("self", "cls"):
            obj = frame.f_locals.get(args.pop(0))
            owner = obj if isinstance(obj, type) and code.co_varnames[0] == "cls" else type(obj)
        parts = qualname.split(".")
        defined_in = parts[-2] if len(parts) > 1 and parts[-2] != "<locals>" else None
        if owner is not None:
            participant = owner.__name__
        elif defined_in:  # a staticmethod
            participant = defined_in
        else:
            participant = frame.f_globals["__name__"].rsplit(".", 1)[-1]
        in_package = owner is not None and owner.__module__.startswith(self.package)
        is_dunder = name.startswith("__") and name.endswith("__")
        hidden = (
            name.startswith("<")
            or (is_dunder and not (name == "__init__" and in_package))
            or (name.startswith("_") and not is_dunder and not self.include_private)
        )
        label = "create" if name == "__init__" else name
        if owner is not None and defined_in and defined_in != owner.__name__:
            label = f"{defined_in}.{label}"  # an inherited method, e.g. super().__init__
        return Call(participant, f"{label}({', '.join(args)})", hidden, name == "__init__")


def visible(node: Call) -> list[Call]:
    """The node's children, with hidden calls replaced by their own visible children."""
    out: list[Call] = []
    for child in node.children:
        out.extend(visible(child) if child.hidden else [child])
    return out


def signature(node: Call, depth: int, max_depth: int | None) -> tuple:
    kids = [] if max_depth is not None and depth >= max_depth else visible(node)
    return (
        node.participant,
        node.label,
        node.result,
        *(signature(k, depth + 1, max_depth) for k in kids),
    )


def repeats(keys: list[tuple]) -> list[tuple[int, int, int]]:
    """Split siblings into (start, period, count) groups, folding runs of identical calls."""
    groups, i = [], 0
    while i < len(keys):
        best = (1, 1)
        for period in range(1, MAX_PERIOD + 1):
            count = 1
            while keys[i + count * period : i + (count + 1) * period] == keys[i : i + period]:
                count += 1
            if count > 1 and period * count > best[0] * best[1]:
                best = (period, count)
        groups.append((i, *best))
        i += best[0] * best[1]
    return groups


def emit_calls(
    caller: str, node: Call, depth: int, max_depth: int | None, out: list[str], seen: list[str]
) -> None:
    if max_depth is not None and depth >= max_depth:
        return
    kids = visible(node)
    keys = [signature(k, depth + 1, max_depth) for k in kids]
    for start, period, count in repeats(keys):
        if count > 1:
            out.append(f"loop {count} times")
        for kid in kids[start : start + period]:
            if kid.participant not in seen:
                seen.append(kid.participant)
            src, dst = alias(caller), alias(kid.participant)
            out.append(f"{src} -> {dst} : {kid.label}")
            emit_calls(kid.participant, kid, depth + 1, max_depth, out, seen)
            if kid.result and not (kid.creates and not kid.result.startswith("raise")):
                out.append(f"{dst} --> {src} : {kid.result}")
        if count > 1:
            out.append("end")


def sequence(args: argparse.Namespace) -> tuple[list[str], int]:
    import pytest

    recorder = Recorder(args.package, args.include_private)

    class Plugin:
        failed: str | None = None
        ran = False

        @pytest.hookimpl(wrapper=True)
        def pytest_runtest_call(self, item: pytest.Item) -> Any:
            recorder.start()
            try:
                return (yield)
            finally:
                recorder.stop()

        def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
            self.ran |= report.when == "call"
            if report.failed and self.failed is None:
                self.failed = report.when

    plugin = Plugin()
    with contextlib.redirect_stdout(sys.stderr):  # keep stdout for the diagram
        code = pytest.main([args.nodeid, "-q", "-p", "no:cacheprovider"], plugins=[plugin])
    if not plugin.ran and plugin.failed is None:
        sys.exit(f"asbuilt: no test ran for {args.nodeid!r} (pytest exit code {int(code)})")
    body: list[str] = []
    seen = ["Test"]
    emit_calls("Test", recorder.root, 0, args.max_depth, body, seen)
    lines = ["@startuml", f"title {args.title or args.nodeid}", "autonumber", "actor Test"]
    lines += [f'participant "{name}" as {alias(name)}' for name in seen[1:]]
    lines += body
    if plugin.failed:
        lines.append(f"note over Test : test failed (in {plugin.failed})")
    return [*lines, "@enduml"], 1 if plugin.failed else 0


# --------------------------------------------------------------------------- classes


def text(annotation: object) -> str:
    """An annotation as short source text: `judgelab.runner.TargetResult` -> `TargetResult`."""
    raw = annotation if isinstance(annotation, str) else inspect.formatannotation(annotation)
    short = re.sub(r"\b(?:[a-z_]\w*\.)+(?=[A-Za-z_])", "", raw)
    return short.replace("{", "(").replace("}", ")").replace("[[", "[ [")  # [[ is a URL


def string_annotations(obj: object) -> dict[str, str]:
    """`obj`'s own annotations as source strings (without evaluating them on 3.14+)."""
    return annotationlib.get_annotations(obj, format=annotationlib.Format.STRING)


def render_signature(fn: Any, skip_first: bool, name: str | None = None) -> str:
    """`name(param: Type, *, kw: Type): Return`, without defaults (they are values)."""
    sig = inspect.signature(fn, annotation_format=annotationlib.Format.STRING)
    params, star = list(sig.parameters.values())[int(skip_first) :], False
    parts = []
    for p in params:
        if p.kind is p.KEYWORD_ONLY and not star:
            parts.append("*")
        star |= p.kind in (p.KEYWORD_ONLY, p.VAR_POSITIONAL)
        prefix = {p.VAR_POSITIONAL: "*", p.VAR_KEYWORD: "**"}.get(p.kind, "")
        ann = "" if p.annotation is p.empty else f": {text(p.annotation)}"
        parts.append(f"{prefix}{p.name}{ann}")
    ret = "" if sig.return_annotation is sig.empty or name else f": {text(sig.return_annotation)}"
    return f"{name or fn.__name__}({', '.join(parts)}){ret}"


def class_body(cls: type) -> list[str]:
    if issubclass(cls, enum.Enum):
        return [f"  {member.name}" for member in cls]
    lines = []
    for name, ann in string_annotations(cls).items():
        visibility = "-" if name.startswith("_") else "+"
        static = "{static} " if "ClassVar" in ann else ""
        lines.append(f"  {static}{visibility} {name}: {text(ann)}")
    for name, attr in vars(cls).items():
        if isinstance(attr, property) and attr.fget and not name.startswith("_"):
            ret = string_annotations(attr.fget).get("return", "")
            lines.append(f"  + {name}: {text(ret)} «property»")
            continue
        fn = attr.__func__ if isinstance(attr, (staticmethod, classmethod)) else attr
        generated = inspect.isfunction(fn) and fn.__code__.co_filename.startswith("<")
        if not inspect.isfunction(fn) or generated or (name.startswith("_") and name != "__init__"):
            continue
        mods = "{abstract} " if getattr(fn, "__isabstractmethod__", False) else ""
        mods += "{static} " if isinstance(attr, (staticmethod, classmethod)) else ""
        shown = cls.__name__ if name == "__init__" else None  # UML constructor, not __init__
        lines.append(f"  {mods}+ {render_signature(fn, not isinstance(attr, staticmethod), shown)}")
    return lines


def relations(cls: type, known: dict[str, type], package: str) -> list[str]:
    lines = [
        f"{alias(base.__name__)} <|-- {alias(cls.__name__)}"
        for base in cls.__bases__
        if base.__module__.startswith(package)
    ]
    for name, ann in string_annotations(cls).items():
        for target in dict.fromkeys(re.findall(r"[A-Za-z_]\w*", ann)):
            if target not in known or known[target] is cls:
                continue
            many = re.search(
                rf"\b(list|tuple|set|frozenset|Sequence|Iterable)\[[^\]]*\b{target}\b", ann
            )
            optional = re.search(r"\bNone\b|Optional\[", ann)
            mult = "*" if many else "0..1" if optional else "1"
            lines.append(f'{alias(cls.__name__)} --> "{mult}" {alias(target)} : {name}')
    return lines


def header(cls: type) -> str:
    """`abstract class X`, `enum X <<enum>>`, `class X <<dataclass(frozen)>>`, ..."""
    if issubclass(cls, enum.Enum):
        return f"enum {alias(cls.__name__)} <<enum>>"
    kind = "abstract class" if inspect.isabstract(cls) else "class"
    stereo = ""
    if dataclasses.is_dataclass(cls):
        stereo = " <<dataclass(frozen)>>" if cls.__dataclass_params__.frozen else " <<dataclass>>"
    elif issubclass(cls, BaseException):
        stereo = " <<exception>>"
    return f"{kind} {alias(cls.__name__)}{stereo}"


def classes(args: argparse.Namespace) -> tuple[list[str], int]:
    modules = [importlib.import_module(name) for name in args.modules]
    known = {
        obj.__name__: obj
        for mod in list(sys.modules.values())
        if mod and mod.__name__.startswith(args.package)
        for obj in vars(mod).values()
        if inspect.isclass(obj) and obj.__module__.startswith(args.package)
    }
    lines = [
        "@startuml",
        "set namespaceSeparator none",
        "hide empty members",
        "hide <<functions>> circle",
    ]
    links: list[str] = []
    for mod in modules:
        lines.append(f'package "{mod.__name__}" {{')
        for obj in vars(mod).values():
            if not inspect.isclass(obj) or obj.__module__ != mod.__name__:
                continue
            body = class_body(obj)
            lines.append(f"  {header(obj)}" + (" {" if body else ""))
            if body:
                lines += [f"  {line}" for line in body] + ["  }"]
            links += relations(obj, known, args.package)
        functions = [
            f"    + {render_signature(fn, False)}"
            for name, fn in vars(mod).items()
            if inspect.isfunction(fn) and fn.__module__ == mod.__name__ and not name.startswith("_")
        ]
        if functions:
            short = mod.__name__.rsplit(".", 1)[-1]
            lines += [f'  class "{short} functions" as {alias(mod.__name__)}_fns <<functions>> {{']
            lines += functions + ["  }"]
        lines.append("}")
    return [*lines, *links, "@enduml"], 0


# --------------------------------------------------------------------------- command line


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    seq = sub.add_parser("sequence", help="sequence diagram of one pytest test")
    seq.add_argument("nodeid")
    seq.add_argument("--include-private", action="store_true")
    seq.add_argument("--max-depth", type=int, default=None)
    seq.add_argument("--title")
    cls = sub.add_parser("classes", help="class diagram of the given modules")
    cls.add_argument("modules", nargs="+")
    for p in (seq, cls):
        p.add_argument("-o", "--output", help="write here instead of stdout")
        p.add_argument("--package", default="judgelab", help="only draw this package's code")
    args = parser.parse_args(argv)
    lines, status = sequence(args) if args.command == "sequence" else classes(args)
    output = "\n".join(lines) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        sys.stdout.write(output)
    return status


if __name__ == "__main__":
    sys.exit(main())
