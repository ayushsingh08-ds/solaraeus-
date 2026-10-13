"""Stage-1 read-only inventory of the SOLARAEUS engine.

Produces, under ``results/raw/stage_1/``:
  * ``inventory.md``   -- per-module table (purpose, LOC, fan-in, tests, status)
  * ``inventory.json`` -- the same data, machine-readable
  * ``legacy_refs.md`` -- every church-street / legacy-site / viewer reference

Nothing is imported and nothing is modified: the analysis is purely static
(AST + regex) so it is safe to run on any tree. ``fan_in`` counts the number of
files under src/, tests/, scripts/, examples/, tools/ that import the module
(either the module itself or its parent package). ``tests`` lists test modules
that import it.

Usage:  python tools/stage1_inventory.py
"""
from __future__ import annotations

import ast
import json
import os
import platform
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "results", "raw", "stage_1")
SCAN_DIRS = ["src", "tests", "scripts", "examples", "tools"]

LEGACY_RE = re.compile(r"church[ _]?street|bengaluru|BLR_SHADE|12\.9749|77\.6054", re.I)
VIEWER_RE = re.compile(r"simulation_3d|three\.min\.js|\bThree\.js\b|webgl|glsl|"
                       r"viewer_app|heatmapShader", re.I)
LEGACY_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules"}


def git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def parse(path: str) -> dict:
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        return {"error": str(e)}
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return {"error": f"SyntaxError: {e}", "loc": len(text.splitlines())}
    doc = (ast.get_docstring(tree) or "").strip()
    classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
    funcs = [n.name for n in tree.body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    mods: list[str] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            mods.append(n.module)
        elif isinstance(n, ast.Import):
            mods.extend(a.name for a in n.names)
    return {
        "doc": doc.splitlines()[0] if doc else "",
        "classes": classes, "funcs": funcs, "imports": mods,
        "loc": len(text.splitlines()), "text": text,
    }


def dotted_for(path: str) -> str:
    rel = os.path.relpath(path, SRC).replace("\\", "/")
    if rel.endswith("/__init__.py"):
        rel = rel[: -len("/__init__.py")]
    elif rel.endswith(".py"):
        rel = rel[:-3]
    return rel.replace("/", ".")


def iter_py(dirs):
    for d in dirs:
        base = os.path.join(ROOT, d)
        for dirpath, dirnames, files in os.walk(base):
            dirnames[:] = [x for x in dirnames if x not in LEGACY_SKIP_DIRS]
            for f in files:
                if f.endswith(".py"):
                    yield os.path.join(dirpath, f)


def main() -> int:
    os.makedirs(OUT, exist_ok=True)

    pkg_root = os.path.join(SRC, "solaraeus")
    modules = []
    for path in sorted(iter_py(["src/solaraeus"])):
        info = parse(path)
        dotted = dotted_for(path)
        modules.append({"file": os.path.relpath(path, ROOT).replace("\\", "/"),
                        "dotted": dotted, **{k: v for k, v in info.items() if k != "text"}})

    # Collect importers (fan-in) and test coverage.
    importer_files = {}
    for path in iter_py(SCAN_DIRS):
        info = parse(path)
        if "imports" not in info:
            continue
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        for m in info["imports"]:
            if m == "solaraeus" or m.startswith("solaraeus."):
                importer_files.setdefault(m, set()).add(rel)

    def fan_in_and_tests(dotted: str, is_pkg: bool):
        parents = [dotted] + [".".join(dotted.split(".")[:i])
                              for i in range(len(dotted.split(".")), 0, -1)]
        hits = set()
        for p in parents:
            hits |= importer_files.get(p, set())
        src_test_scripts = {h for h in hits if not h.endswith(os.path.basename(dotted) + ".py")}
        tests = sorted(h for h in hits if h.startswith("tests/"))
        others = sorted(h for h in hits if not h.startswith("tests/")
                        and h != os.path.relpath(
                            os.path.join(SRC, dotted.replace(".", os.sep) + ".py"),
                            ROOT).replace("\\", "/"))
        # exclude self
        self_rel = os.path.relpath(
            os.path.join(SRC, dotted.replace(".", os.sep) + ".py"), ROOT).replace("\\", "/")
        others = [o for o in others if o != self_rel]
        # for packages, path is .../__init__.py
        self_rel2 = os.path.relpath(
            os.path.join(SRC, dotted.replace(".", os.sep), "__init__.py"),
            ROOT).replace("\\", "/")
        others = [o for o in others if o != self_rel2]
        return len(others), tests, others

    for mod in modules:
        n, tests, others = fan_in_and_tests(mod["dotted"], mod["dotted"].endswith("__init__"))
        mod["fan_in"] = n
        mod["tests"] = tests
        mod["importers_head"] = others[:5]
        if mod.get("error"):
            mod["status"] = "BROKEN (parse error)"
        elif n == 0 and not tests and mod["dotted"].count(".") >= 1:
            mod["status"] = "UNUSED (no importer)"
        else:
            mod["status"] = "works (imported)"

    # ---- legacy / viewer references across the whole repo -------------------
    legacy_hits, viewer_hits = [], []
    for dirpath, dirnames, files in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in LEGACY_SKIP_DIRS]
        for f in files:
            path = os.path.join(dirpath, f)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            if rel.startswith("results/") or rel.startswith("data/") \
                    or rel.startswith("bengaluru_church_street_manual_handoff_v2/"):
                continue  # frozen artifacts / pinned inputs: listed separately
            if os.path.getsize(path) > 2_000_000:
                continue
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if LEGACY_RE.search(text):
                for i, line in enumerate(text.splitlines(), 1):
                    if LEGACY_RE.search(line):
                        legacy_hits.append((rel, i, line.strip()[:160]))
            if VIEWER_RE.search(text):
                for i, line in enumerate(text.splitlines(), 1):
                    if VIEWER_RE.search(line):
                        viewer_hits.append((rel, i, line.strip()[:160]))

    legacy_files = sorted({h[0] for h in legacy_hits})
    viewer_files = sorted({h[0] for h in viewer_hits})

    # ---- write markdown ----------------------------------------------------
    with open(os.path.join(OUT, "inventory.md"), "w", encoding="utf-8") as fh:
        fh.write("# Stage-1 module inventory (static, read-only)\n\n")
        fh.write(f"- generated: {__import__('time').strftime('%Y-%m-%dT%H:%M:%SZ', __import__('time').gmtime())}\n")
        fh.write(f"- git: {git('rev-parse', 'HEAD')}\n")
        fh.write(f"- python: {platform.python_version()}\n")
        fh.write(f"- modules: {len(modules)}\n\n")
        fh.write("| file | purpose (docstring) | LOC | classes | funcs | fan-in | tests covering | status |\n")
        fh.write("|---|---|---|---|---|---|---|---|\n")
        for m in modules:
            fh.write(f"| `{m['file']}` | {m['doc'][:90] or '—'} | {m.get('loc','')} | "
                     f"{len(m.get('classes',[]))} | {len(m.get('funcs',[]))} | {m.get('fan_in','')} | "
                     f"{', '.join(os.path.basename(t) for t in m.get('tests',[])) or '—'} | {m['status']} |\n")

    with open(os.path.join(OUT, "legacy_refs.md"), "w", encoding="utf-8") as fh:
        fh.write("# Stage-1 legacy-site / viewer references\n\n")
        fh.write("Scanned: src, tests, scripts, examples, tools, docs, configs, root docs.\n")
        fh.write("Excluded (listed separately, treated as frozen): results/, data/, "
                 "bengaluru_church_street_manual_handoff_v2/\n\n")
        fh.write(f"## Legacy-site references ({len(legacy_files)} files, {len(legacy_hits)} lines)\n\n")
        for rel in legacy_files:
            fh.write(f"- `{rel}`\n")
        fh.write(f"\n## Viewer references ({len(viewer_files)} files, {len(viewer_hits)} lines)\n\n")
        for rel in viewer_files:
            fh.write(f"- `{rel}`\n")

    with open(os.path.join(OUT, "inventory.json"), "w", encoding="utf-8") as fh:
        json.dump({"git": git("rev-parse", "HEAD"), "modules": modules,
                   "legacy_files": legacy_files, "viewer_files": viewer_files},
                  fh, indent=2)

    print(f"modules: {len(modules)}")
    print(f"legacy ref files: {len(legacy_files)}  (lines {len(legacy_hits)})")
    print(f"viewer ref files: {len(viewer_files)}  (lines {len(viewer_hits)})")
    print("wrote:", os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
