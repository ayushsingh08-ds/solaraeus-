"""Audit the automated unused-import removal against the pre-change revision.

Why this exists
---------------
Phase 1 removed unused imports automatically (ruff F401).  F401 treats a name
that appears only inside a *string annotation* (``x: "List[int]"`` in a module
without ``from __future__ import annotations``) as unused, so the rewrite can
delete an import that the module still needs at runtime.  The test suite and the
golden master do not necessarily execute those annotated functions, so a silent
breakage survives both.

This script is the independent check: it compares the imported names declared at
HEAD with the imported names declared now, and reports every removed name that
still occurs as an identifier in the current file.

Usage
-----
    python tools/golden/audit_removed_imports.py            # human report
    python tools/golden/audit_removed_imports.py --exit-code  # non-zero if findings
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

# Comment lines are excluded: prose mentioning a name is not a use of it.
NOQA_RE = re.compile(r"#.*$")


def _run_git(*args: str) -> str:
    """Return stdout of a git command, or "" when the object is absent."""
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def imported_names(source: str) -> set[str]:
    """Top-level binding names introduced by import statements in *source*."""
    names: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                names.add(alias.asname or alias.name)
    return names


def occurrences(source: str, name: str) -> list[int]:
    """Line numbers where *name* occurs as a word outside comments."""
    pattern = re.compile(rf"\b{re.escape(name)}\b")
    lines: list[int] = []
    for number, raw in enumerate(source.splitlines(), start=1):
        if pattern.search(NOQA_RE.sub("", raw)):
            lines.append(number)
    return lines


def is_docstring_or_comment(source: str, line: int) -> bool:
    """True when *line* (1-indexed) is inside a string literal or a comment.

    Such an occurrence is documentation, not a use: removing the import is safe.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            if start <= line <= end:
                return True
    return False


def is_import_line(source: str, line: int) -> bool:
    """True when *line* (1-indexed) is an import statement or its continuation.

    The name still occurring there means it was mentioned as part of some *other*
    import path (``from shapely.geometry import ...`` mentions ``shapely``), not
    that the removed binding is still referenced.  Without this filter every
    removed package alias is reported as a false positive.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            if start <= line <= end:
                return True
    return False


def changed_python_files() -> list[str]:
    """Paths of Python files modified in the working tree (tracked only)."""
    out = _run_git("diff", "--name-only", "--diff-filter=d")
    return [p for p in out.splitlines() if p.endswith(".py")]


def main() -> int:
    """Print the audit and return 1 when a removed name is still referenced."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exit-code", action="store_true")
    args = parser.parse_args()

    findings: list[tuple[str, str, list[int]]] = []
    documentary: list[tuple[str, str]] = []
    files = changed_python_files()
    for rel in files:
        current = (REPO / rel).read_text(encoding="utf-8", errors="replace")
        before = _run_git("show", f"HEAD:{rel}")
        if not before:
            continue  # newly added file: nothing was removed
        removed = imported_names(before) - imported_names(current)
        for name in sorted(removed):
            hits = occurrences(current, name)
            if not hits:
                continue
            code_hits = [
                n
                for n in hits
                if not is_docstring_or_comment(current, n) and not is_import_line(current, n)
            ]
            if code_hits:
                findings.append((rel, name, code_hits))
            elif hits:
                documentary.append((rel, name))

    print(f"changed python files examined : {len(files)}")
    print(f"removed name still used in CODE : {len(findings)}")
    print(f"removed name only in docstring/comment (safe) : {len(documentary)}")
    if findings:
        print("\nSUSPECT REMOVALS (dropped but referenced outside prose):")
        for rel, name, hits in findings:
            shown = ", ".join(str(n) for n in hits[:6])
            print(f"  {rel}: {name}  -> lines {shown}")
    return 1 if findings and args.exit_code else 0


if __name__ == "__main__":
    raise SystemExit(main())
