"""Cycle break, step 1: extract the edit classes and `SimulationResult`.

Why
---
`PROJECT_STRUCTURE.md` §9.1 records exactly one real import cycle (9 files).
Its root cause is that `incremental/update.py` is three things at once: the
edit data model, the incremental algorithm, and the backend dispatcher.
`incremental/certificate.py` needs `GeometricEdit` from `update.py`, while
`update.py` needs `generate_error_certificate` from `certificate.py`; the cycle
only imports because the latter is done inside a function body.

This codemod performs the extraction as a **pure move**:

* `incremental/update.py` -> `incremental/edits.py` gains
  `GeometricEdit`, `AddBuildingEdit`, `RemoveBuildingEdit`, `ChangeHeightEdit`,
  `MoveBuildingEdit` (byte-identical slices, no edits to the code itself).
* `reference/full_recompute.py` -> `reference/result.py` gains
  `SimulationResult` (byte-identical slice).

and then rewrites the imports (AST-verified: every edited file is re-parsed).

Usage
-----
    python tools/migrations/cycle_break_edits.py --check    # report only
    python tools/migrations/cycle_break_edits.py            # apply
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src" / "urban_comfort"

UPDATE = SRC / "incremental" / "update.py"
EDITS = SRC / "incremental" / "edits.py"
FULL_RECOMPUTE = SRC / "reference" / "full_recompute.py"
RESULT = SRC / "reference" / "result.py"

EDITS_HEADER = '''"""Geometric edit types: the *what changed* half of the incremental API.

An edit is a small, serializable description of a change to a `Scene`.  Each
edit knows how to apply itself and how to report the 3-D volume of space whose
geometry changed, which is what the affected-region and certificate code needs
in order to bound the error.  `incremental/certificate.py` depends on this
module and this module depends on nothing in `incremental/`, which is what
keeps the certificate path free of import cycles.

Split out of `incremental/update.py` during the cycle break; the class bodies
are byte-identical to the originals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from urban_comfort.geometry.primitives import Building
from urban_comfort.geometry.scene import Scene

'''

RESULT_HEADER = '''"""`SimulationResult`: the single output contract of the whole engine.

Every solver -- full reference, exact incremental, certified incremental,
CPU or GPU -- returns one of these.  Seven NumPy arrays plus a metadata dict,
with no disk I/O in between.  `incremental/` needs the *type* without needing
the reference solver, so it lives here on its own to keep the import graph
acyclic.

Split out of `reference/full_recompute.py`; byte-identical to the original.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import numpy as np

'''

# --- import rewrites -------------------------------------------------------
# (old dotted module, symbol) -> new dotted module, applied line by line to
# ``from <old> import <symbols>`` statements.
EDITS_MODULE = "urban_comfort.incremental.edits"
UPDATE_MODULE = "urban_comfort.incremental.update"
RESULT_MODULE = "urban_comfort.reference.result"
FULL_MODULE = "urban_comfort.reference.full_recompute"

EDIT_SYMBOLS = {
    "GeometricEdit",
    "AddBuildingEdit",
    "RemoveBuildingEdit",
    "ChangeHeightEdit",
    "MoveBuildingEdit",
}

IMPORT_RE = re.compile(r"^(?P<indent>\s*)from (?P<mod>[A-Za-z_][\w.]*) import (?P<rest>.*)$")


def read_exact(path: Path) -> str:
    """Read a file without newline translation, so CRLF markers still match."""
    with path.open(encoding="utf-8", newline="") as handle:
        return handle.read()


def write_exact(path: Path, text: str) -> None:
    """Write a file without newline translation (keeps the original line endings)."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def split_symbols(rest: str) -> tuple[list[str], str]:
    """Split ``a, b, c  # comment`` into (['a','b','c'], '  # comment')."""
    body, _, comment = rest.partition("#")
    body = body.strip().rstrip(",").strip()
    if body.startswith("("):
        body = body.strip("()").strip().rstrip(",")
    symbols = [s.strip() for s in body.replace("\n", " ").split(",") if s.strip()]
    return symbols, ("  #" + comment if comment else "")


# Only these two modules are rewritten, so the blast radius is exactly the
# files that import the moved symbols.
SOURCE_MODULES = {UPDATE_MODULE, FULL_MODULE}

# A parenthesised import block for one of the source modules.
PAREN_RE = re.compile(
    r"^(?P<indent>[ \t]*)from (?P<mod>%s) import \(\r?\n"
    r"(?P<body>(?:[ \t]+[^\n]*\r?\n)*?)"
    r"[ \t]*\)[ \t]*(?P<eol>\r?\n)" % "|".join(re.escape(m) for m in sorted(SOURCE_MODULES)),
    re.MULTILINE,
)


def _targets(module: str, symbols: list[str]) -> dict[str, list[str]]:
    """Group import symbols by the module they should be imported from."""
    targets: dict[str, list[str]] = {}
    for symbol in symbols:
        if symbol in EDIT_SYMBOLS and module == UPDATE_MODULE:
            targets.setdefault(EDITS_MODULE, []).append(symbol)
        elif symbol == "SimulationResult" and module == FULL_MODULE:
            targets.setdefault(RESULT_MODULE, []).append(symbol)
        else:
            targets.setdefault(module, []).append(symbol)
    return targets


def _render(indent: str, targets: dict[str, list[str]], eol: str) -> str:
    """Render the (possibly split) import statements for one source import."""
    lines = [f"{indent}from {mod} import {', '.join(syms)}{eol}" for mod, syms in targets.items()]
    return "".join(lines)


def rewrite_imports(path: Path, dry_run: bool) -> int:
    """Move edit/result symbols onto their new modules in one file."""
    text = read_exact(path)
    original = text

    def paren_repl(match: re.Match[str]) -> str:
        symbols = [
            part.strip().rstrip(",")
            for part in match.group("body").replace("\r", "").splitlines()
            if part.strip() and not part.strip().startswith("#")
        ]
        targets = _targets(match.group("mod"), symbols)
        if list(targets) == [match.group("mod")]:
            return match.group(0)
        return _render(match.group("indent"), targets, match.group("eol"))

    text = PAREN_RE.sub(paren_repl, text)

    out: list[str] = []
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        newline = line[len(stripped) :] or "\n"
        match = IMPORT_RE.match(stripped)
        if match is None or match.group("mod") not in SOURCE_MODULES:
            out.append(line)
            continue
        symbols, comment = split_symbols(match.group("rest"))
        if not symbols:
            out.append(line)
            continue
        targets = _targets(match.group("mod"), symbols)
        if list(targets) == [match.group("mod")]:
            out.append(line)
            continue
        out.append(_render(match.group("indent"), targets, newline))
    text = "".join(out)

    if text == original:
        return 0
    ast.parse(text)  # raise if we produced something unparsable
    if not dry_run:
        write_exact(path, text)
    return 1


def slice_class(text: str, class_name: str, next_marker: str) -> tuple[str, str]:
    """Return (block, remainder) for one class, sliced byte-exactly."""
    start_marker = f"@dataclass\r\nclass {class_name}"
    start = text.find(start_marker)
    if start < 0:
        start_marker = f"@dataclass\nclass {class_name}"
        start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"could not find class {class_name}")
    end = text.find(next_marker, start)
    if end < 0:
        raise SystemExit(f"could not find marker after {class_name}")
    return text[start:end], text[:start] + text[end:]


def extract_edits(dry_run: bool) -> None:
    """Move the five building edit classes out of update.py."""
    if EDITS.exists() and not dry_run:
        print("incremental/edits.py already exists; skipping extraction")
        return
    text = read_exact(UPDATE)
    block, remainder = slice_class(
        text, "GeometricEdit", "@dataclass\r\nclass IncrementalUpdateResult"
    )
    assert "class MoveBuildingEdit" in block, "slice is missing edit classes"
    assert "class IncrementalUpdateResult" not in block

    eol = "\r\n" if "\r\n" in text else "\n"
    anchor = f"from urban_comfort.geometry.primitives import Building{eol}"
    if anchor not in remainder:
        # `Building` may be unused once the classes leave; fall back to the
        # scene import, which the edit classes and update.py both need.
        anchor = f"from urban_comfort.geometry.scene import Scene{eol}"
    assert anchor in remainder, "no anchor line found for the edits import"
    insertion = (
        f"from urban_comfort.incremental.edits import ({eol}"
        f"    AddBuildingEdit,{eol}"
        f"    ChangeHeightEdit,{eol}"
        f"    GeometricEdit,{eol}"
        f"    MoveBuildingEdit,{eol}"
        f"    RemoveBuildingEdit,{eol}"
        f"){eol}"
    )
    new_update = remainder.replace(anchor, anchor + insertion, 1)
    assert new_update != remainder, "failed to insert the edits import"

    if not dry_run:
        write_exact(EDITS, EDITS_HEADER + block)
        write_exact(UPDATE, new_update)
        ast.parse(read_exact(EDITS))
        ast.parse(new_update)
    print(f"edits.py: {len(block)} chars moved out of update.py")


def extract_result(dry_run: bool) -> None:
    """Move SimulationResult out of full_recompute.py."""
    if RESULT.exists() and not dry_run:
        print("reference/result.py already exists; skipping extraction")
        return
    text = read_exact(FULL_RECOMPUTE)
    next_marker = "def full_recompute(scene: Scene, weather: Weather,"
    block, remainder = slice_class(text, "SimulationResult", next_marker)
    assert "class SimulationResult" in block

    eol = "\r\n" if "\r\n" in text else "\n"
    anchor = f"from urban_comfort.geometry.scene import Scene{eol}"
    assert anchor in remainder, "no anchor line found for the result import"
    insertion = f"from urban_comfort.reference.result import SimulationResult{eol}"
    remainder = remainder.replace(anchor, anchor + insertion, 1)
    if not dry_run:
        write_exact(RESULT, RESULT_HEADER + block.rstrip("\r\n") + "\n")
        write_exact(FULL_RECOMPUTE, remainder)
        ast.parse(read_exact(RESULT))
        ast.parse(remainder)
    print(f"result.py: {len(block)} chars moved out of full_recompute.py")


def main() -> int:
    """Run the migration."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report only, change nothing")
    args = parser.parse_args()
    dry_run = args.check

    extract_edits(dry_run)
    extract_result(dry_run)

    changed = 0
    for path in sorted(REPO_ROOT.glob("**/*.py")):
        if any(
            part in {".git", "archive", "node_modules", "upstream", "dataset_prep"}
            for part in path.parts
        ):
            continue
        if path in {EDITS, RESULT}:
            continue
        try:
            changed += rewrite_imports(path, dry_run)
        except SyntaxError as exc:
            print(f"REFUSING: {path} would not parse: {exc}", file=sys.stderr)
            return 1
    print(f"{'would rewrite' if dry_run else 'rewrote'} imports in {changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
