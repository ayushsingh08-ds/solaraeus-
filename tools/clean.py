"""Remove local caches and generated artifacts.

Only ever deletes paths that are git-ignored or explicitly listed here, so it
can never destroy tracked evidence. Reports what it removed and how much space
that reclaimed.

Usage
-----
    python tools/clean.py            # dry run: show what would be removed
    python tools/clean.py --yes      # actually remove
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories that are always safe to remove (caches, build output).
CACHE_DIRS = ["__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".coverage"]
GENERATED_DIRS = ["tools/golden/candidate", "artifacts", "viewer/node_modules", "viewer/dist"]
GENERATED_FILES = ["requirements.lock.tmp"]


def is_git_ignored(path: Path) -> bool:
    """True if git ignores this path (so deleting it cannot lose tracked data)."""
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", str(path)],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    return result.returncode == 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="actually delete")
    args = parser.parse_args()

    targets: list[Path] = []

    for pattern in CACHE_DIRS:
        if pattern.startswith("."):
            for candidate in REPO_ROOT.rglob(f"*{pattern}*"):
                if candidate.is_dir() or candidate.is_file():
                    targets.append(candidate)
        else:
            targets.extend(p for p in REPO_ROOT.rglob(pattern) if p.is_dir())

    for rel in GENERATED_DIRS:
        candidate = REPO_ROOT / rel
        if candidate.exists():
            targets.append(candidate)
    for rel in GENERATED_FILES:
        candidate = REPO_ROOT / rel
        if candidate.exists():
            targets.append(candidate)

    # De-duplicate, drop nested paths, and never touch tracked content.
    unique = sorted({p for p in targets if p != REPO_ROOT})
    pruned: list[Path] = []
    for path in unique:
        if any(path.is_relative_to(parent) for parent in pruned):
            continue
        pruned.append(path)

    total_bytes = 0
    for path in pruned:
        if path.is_file():
            size = path.stat().st_size
        else:
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        total_bytes += size
        tracked = not is_git_ignored(path) and (path.is_dir() or path.is_file())
        flag = "TRACKED?" if tracked else "ignored"
        print(f"  [{flag}] {path.relative_to(REPO_ROOT)}")
        if args.yes and not tracked:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)

    print(f"\n{len(pruned)} paths, {total_bytes / 1e6:.1f} MB")
    if not args.yes:
        print("dry run - re-run with --yes to delete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
