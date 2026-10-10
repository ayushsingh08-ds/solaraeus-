"""Import-cycle and layering checker (Tarjan strongly-connected components).

Scans every Python file under a set of roots with the ast module, resolves
intra-project imports to real files, and reports:

  1. every strongly-connected component with more than one file (a true cycle);
  2. self-loops;
  3. imports that occur *inside a function body* (the usual way a project hides
     a cycle from the interpreter while keeping it in the source).

Two kinds of cycle are reported separately, because they have different
consequences:

  * **top-level cycles** are fatal: the interpreter cannot build the modules and
    `import` raises.  The gate fails on these, and the post-overhaul target is
    zero.
  * **lazy cycles** exist only through imports written *inside a function body*.
    They import cleanly as long as nothing calls the function during module
    initialisation.  `--strict` counts them as failures too.  They are the
    deliberate shape of the optional-GPU dispatch (`full_recompute` must not
    import CuPy at module scope), so a small number is expected and is listed
    rather than hidden.

Usage
-----
    python tools/golden/cycle_check.py [--roots src] [--quiet] [--strict]
"""

from __future__ import annotations

import argparse
import ast
import collections
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def module_name_of(path: Path, roots: list[Path]) -> str | None:
    """Map a file path under a src root to its dotted module name."""
    for root in roots:
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if rel.suffix != ".py":
            continue
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts) if parts else None
    return None


def scan(root_dirs: list[Path]):
    """Return (edges, function_local_edges) as dicts of file -> set of files."""
    modules: dict[str, str] = {}
    files: list[Path] = []
    for root in root_dirs:
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            files.append(path)
            name = module_name_of(path, root_dirs)
            if name:
                modules[name] = path.as_posix()

    def resolve(dotted: str) -> str | None:
        if dotted in modules:
            return modules[dotted]
        parts = dotted.split(".")
        for i in range(len(parts), 0, -1):
            candidate = ".".join(parts[:i])
            if candidate in modules:
                return modules[candidate]
        return None

    edges: dict[str, set[str]] = collections.defaultdict(set)
    local_edges: dict[str, set[str]] = collections.defaultdict(set)

    for path in files:
        src = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src, str(path))
        except SyntaxError as exc:
            print(f"  [syntax error] {path}: {exc}", file=sys.stderr)
            continue
        rel = path.as_posix()

        # imports at module scope
        top_level: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                top_level.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                top_level.add(("." * node.level) + (node.module or ""))

        # imports anywhere (superset)
        all_imports: set[tuple[str, bool]] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    all_imports.add((a.name, True))
            elif isinstance(node, ast.ImportFrom):
                dotted = ("." * node.level) + (node.module or "")
                all_imports.add((dotted, True))

        def record(owner: str, dotted: str, is_local: bool) -> None:
            """Add one edge from *owner*; ``owner`` is a parameter, not a closure.

            Binding the loop variable through a parameter keeps the function
            independent of when it is called (see ruff B023).
            """
            target = resolve(dotted)
            if target and target != owner:
                edges[owner].add(target)
                if is_local:
                    local_edges[owner].add(target)

        for dotted in top_level:
            record(rel, dotted, False)
        for dotted, _ in all_imports:
            if dotted not in top_level:
                record(rel, dotted, True)

    return edges, local_edges


def tarjan(edges: dict[str, set[str]]) -> list[list[str]]:
    """Return all strongly-connected components (Tarjan, iterative-free recursion)."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    components: list[list[str]] = []
    counter = [0]

    def strongconnect(node: str) -> None:
        index[node] = low[node] = counter[0]
        counter[0] += 1
        stack.append(node)
        on_stack.add(node)
        for neighbour in edges.get(node, ()):  # noqa: B007
            if neighbour not in index:
                strongconnect(neighbour)
                low[node] = min(low[node], low[neighbour])
            elif neighbour in on_stack:
                low[node] = min(low[node], index[neighbour])
        if low[node] == index[node]:
            component = []
            while True:
                member = stack.pop()
                on_stack.discard(member)
                component.append(member)
                if member == node:
                    break
            components.append(component)

    for node in list(edges):
        if node not in index:
            strongconnect(node)
    return components


def main() -> int:
    """CLI entry point; returns 0 when the import graph is acyclic."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", nargs="*", default=["src"])
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--strict", action="store_true", help="also fail on lazy (function-local) cycles"
    )
    args = parser.parse_args()

    root_dirs = [REPO_ROOT / r for r in args.roots]
    edges, local_edges = scan(root_dirs)

    files_count = len({f for f in edges} | {t for ts in edges.values() for t in ts})
    print(
        f"scanned {files_count} modules under {[str(r.relative_to(REPO_ROOT)) for r in root_dirs]}"
    )
    print(f"internal import edges: {sum(len(v) for v in edges.values())}")

    components = tarjan(edges)
    all_cycles = [c for c in components if len(c) > 1]
    # A component is "top-level" (fatal) when it survives deleting the
    # function-local edges; otherwise its back-edges are all lazy.
    top_level_edges = {
        src: {dst for dst in dsts if dst not in local_edges.get(src, set())}
        for src, dsts in edges.items()
    }
    top_level_ids = {tuple(sorted(c)): c for c in tarjan(top_level_edges) if len(c) > 1}
    cycles = [c for c in all_cycles if tuple(sorted(c)) in top_level_ids]
    lazy_cycles = [c for c in all_cycles if tuple(sorted(c)) not in top_level_ids]
    self_loops = [f for f, deps in edges.items() if f in deps]

    def rel(p: str) -> str:
        try:
            return Path(p).relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return p

    if cycles:
        print(f"\nTOP-LEVEL CYCLES FOUND: {len(cycles)}")
        for component in cycles:
            print(f"  cycle ({len(component)} files):")
            for member in sorted(component):
                print(f"      {rel(member)}")
    else:
        print("\ntop-level cycles: none (import graph is acyclic)")

    if lazy_cycles:
        print(f"\nlazy cycles (function-local back-edges only): {len(lazy_cycles)}")
        for component in lazy_cycles:
            print(f"  cycle ({len(component)} files):")
            for member in sorted(component):
                locals_here = sorted(local_edges.get(member, set()) & set(component))
                marker = "  (function-local edge)" if locals_here else ""
                print(f"      {rel(member)}{marker}")

    if self_loops:
        print(f"\nself-loops: {len(self_loops)}")
        for f in self_loops:
            print(f"    {f}")

    print(f"\nfunction-local internal imports: {sum(len(v) for v in local_edges.values())}")
    if not args.quiet and local_edges:
        for src_file in sorted(local_edges):
            if local_edges[src_file]:
                print(f"    {rel(src_file)} -> {[rel(t) for t in sorted(local_edges[src_file])]}")

    failed = bool(cycles or self_loops) or (args.strict and bool(lazy_cycles))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
