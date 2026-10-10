"""Report the exact third-party import surface, split by run-time role.

Role separation matters for packaging: a library import only reachable from a
tool/test is a *dev* dependency, while one reachable from the shipped package is
a runtime dependency.

Usage
-----
    python tools/golden/dep_scan.py
"""

from __future__ import annotations

import ast
import collections
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Map top-level module name -> distribution name on PyPI, where they differ.
DISTRIBUTION = {
    "PIL": "pillow",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "cupy": "cupy-cuda12x",
    "mpl_toolkits": "matplotlib",
    "pythermalcomfort": "pythermalcomfort",
    "shapely": "shapely",
    "rasterio": "rasterio",
    "pyproj": "pyproj",
    "trimesh": "trimesh",
    "mapbox_earcut": "mapbox_earcut",
    "psutil": "psutil",
    "scipy": "scipy",
    "numpy": "numpy",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "pytest": "pytest",
}

STDLIB = set(sys.stdlib_module_names)

ROLES = {
    "runtime": ["src"],
    "scripts": ["scripts"],
    "tests": ["tests"],
    "tools": ["tools"],
}


def scan_role(dirs: list[str]) -> dict[str, set[str]]:
    """Return {module: {importer, ...}} for one role."""
    found: dict[str, set[str]] = collections.defaultdict(set)
    for d in dirs:
        root = REPO_ROOT / d
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), str(path))
            except SyntaxError:
                continue
            seen: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    seen.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.level:  # relative import
                        continue
                    if node.module:
                        seen.add(node.module.split(".")[0])
            for mod in seen:
                found[mod].add(path.relative_to(REPO_ROOT).as_posix())
    return found


def main() -> int:
    """Print the import surface per role and the derived dependency sets."""
    role_imports: dict[str, dict[str, set[str]]] = {
        role: scan_role(dirs) for role, dirs in ROLES.items()
    }

    def third_party(mod: str) -> bool:
        return (
            mod not in STDLIB
            and not mod.startswith("urban_comfort")
            and not mod.startswith("solaraeus")
            and mod != "__future__"
        )

    for role, imports in role_imports.items():
        print("=" * 78)
        print(f"ROLE: {role}")
        print("=" * 78)
        for mod in sorted(imports):
            if third_party(mod):
                files = sorted(imports[mod])
                print(f"  {mod:22s} {len(files):3d} importers   e.g. {files[0]}")
        std = [m for m in sorted(imports) if m in STDLIB]
        print(f"  [stdlib] {len(std)} modules used")

    # Derived sets
    runtime = {m for m in role_imports["runtime"] if third_party(m)}
    scripts = {m for m in role_imports["scripts"] if third_party(m)}
    tests = {m for m in role_imports["tests"] if third_party(m)}
    tools = {m for m in role_imports["tools"] if third_party(m)}

    print()
    print("=" * 78)
    print("DERIVED PACKAGING SETS")
    print("=" * 78)
    print(f"runtime (src only)          : {sorted(runtime)}")
    print(f"scripts-only extras         : {sorted(scripts - runtime)}")
    print(f"tests-only extras           : {sorted(tests - runtime - scripts)}")
    print(f"tools-only extras           : {sorted(tools - runtime - scripts - tests)}")
    print()
    print("PyPI distribution names:")
    for mod in sorted(runtime | scripts | tests | tools):
        print(f"  {mod:22s} -> {DISTRIBUTION.get(mod, mod)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
