"""Record a SHA-256 inventory of every git-tracked file.

Purpose
-------
The overhaul moves, merges and deletes files. This tool freezes the exact
content of every tracked file *before* any change, so REFACTOR_REPORT.md can
prove, file by file, whether content survived (kept / moved / merged / deleted).

Usage
-----
    python tools/golden/inventory.py write   # snapshot -> tools/golden/baseline/inventory.json
    python tools/golden/inventory.py diff    # compare current tree against the snapshot
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOT = Path(__file__).resolve().parent / "baseline" / "inventory.json"


def git_tracked_files() -> list[str]:
    """Return every path tracked by git, as POSIX-style relative paths."""
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return sorted(p for p in out.decode("utf-8").split("\0") if p)


def sha256_of(rel_path: str) -> str:
    """Return the hex SHA-256 of a tracked file's bytes."""
    digest = hashlib.sha256()
    with open(REPO_ROOT / rel_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_snapshot() -> None:
    """Hash every tracked file and persist the inventory."""
    files = git_tracked_files()
    inventory = {rel: sha256_of(rel) for rel in files}
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "git_head": subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip(),
                "file_count": len(inventory),
                "files": inventory,
            },
            handle,
            indent=1,
            sort_keys=True,
        )
    print(f"wrote {len(inventory)} file hashes -> {SNAPSHOT.relative_to(REPO_ROOT)}")


def diff_snapshot() -> int:
    """Report added / removed / content-changed files versus the snapshot."""
    with open(SNAPSHOT, encoding="utf-8") as handle:
        baseline = json.load(handle)["files"]
    current = {rel: sha256_of(rel) for rel in git_tracked_files()}

    added = sorted(set(current) - set(baseline))
    removed = sorted(set(baseline) - set(current))
    changed = sorted(rel for rel in set(current) & set(baseline) if current[rel] != baseline[rel])
    identical = len(set(current) & set(baseline)) - len(changed)

    print(f"identical-content : {identical}")
    print(f"added             : {len(added)}")
    print(f"removed           : {len(removed)}")
    print(f"content-changed   : {len(changed)}")
    for label, rows in (("ADDED", added), ("REMOVED", removed), ("CHANGED", changed)):
        for rel in rows[:200]:
            print(f"  {label}: {rel}")
        if len(rows) > 200:
            print(f"  {label}: ... and {len(rows) - 200} more")
    return 0


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "write"
    if command == "write":
        write_snapshot()
    elif command == "diff":
        raise SystemExit(diff_snapshot())
    else:
        raise SystemExit(f"unknown command {command!r}; use 'write' or 'diff'")
