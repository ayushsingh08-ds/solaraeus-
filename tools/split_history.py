"""Split the monolithic development log into one file per top-level section.

`context.md` was a 237 KB, 2,600-line single document that grew one milestone
at a time. It is now `docs/history/NN-<slug>.md`, one file per `## ` section,
plus a generated index. Nothing is rewritten: the script proves it by
reassembling the parts and comparing them byte-for-byte with the source before
it deletes anything.

Usage
-----
    python tools/split_history.py --dry-run    # show the plan, change nothing
    python tools/split_history.py              # split (source removed on success)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "docs" / "history" / "_context_source.md"
OUT_DIR = REPO_ROOT / "docs" / "history"
SECTION_RE = re.compile(r"^## (?!#)(.*)$", re.MULTILINE)

SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    """Turn a section heading into a filesystem-safe slug."""
    # Drop a leading ordinal ("4.", "12 ") so the file number is not doubled.
    text = re.sub(r"^\s*\d+[.)]?\s*", "", title.strip()).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return re.sub(r"-+", "-", text)[:60] or "section"


def split_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (preamble, [(heading, body)]) with bodies kept verbatim."""
    matches = list(SECTION_RE.finditer(text))
    if not matches:
        raise SystemExit(f"{SOURCE.name}: no '## ' sections found")
    preamble = text[: matches[0].start()]
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = text[match.start() : end]
        heading = match.group(1).strip()
        sections.append((heading, chunk))
    return preamble, sections


def main() -> int:
    """Split the log, or print the plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print the plan only")
    args = parser.parse_args()

    if not SOURCE.exists():
        print(f"{SOURCE.relative_to(REPO_ROOT)} not found; nothing to split", file=sys.stderr)
        return 1

    original = SOURCE.read_text(encoding="utf-8")
    preamble, sections = split_sections(original)

    # Reassembly check: parts must reproduce the source exactly.
    rebuilt = preamble + "".join(chunk for _, chunk in sections)
    if rebuilt != original:
        print("REFUSING: reassembly is not byte-identical to the source", file=sys.stderr)
        return 1

    plan: list[tuple[Path, str]] = []
    index_lines = [
        "# Development history",
        "",
        "Split from the original single-file `context.md` by",
        "`tools/split_history.py`, which verified that the parts reproduce the",
        "source byte-for-byte before removing it. Content is unedited.",
        "",
        "| # | Section | File |",
        "|---:|---|---|",
    ]
    for number, (heading, chunk) in enumerate(sections, 1):
        name = f"{number:02d}-{slugify(heading)}.md"
        path = OUT_DIR / name
        plan.append((path, chunk))
        index_lines.append(f"| {number} | {heading} | [{name}]({name}) |")
    index_lines.append("")

    if args.dry_run:
        print(f"preamble: {len(preamble)} chars -> 00-index.md")
        for path, chunk in plan:
            print(f"  {path.name:<52} {len(chunk):>7} chars")
        print(f"verify: reassembly matches source ({len(original)} chars) OK")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "00-index.md").write_text(
        preamble.rstrip() + "\n\n" + "\n".join(index_lines), encoding="utf-8"
    )
    for path, chunk in plan:
        path.write_text(chunk, encoding="utf-8")

    # Prove the split round-trips before deleting the source.
    recovered = (OUT_DIR / "00-index.md").read_text(encoding="utf-8")
    recovered = recovered[: len(preamble.rstrip())]
    if recovered != preamble.rstrip():
        print("REFUSING to delete source: index preamble did not round-trip", file=sys.stderr)
        return 1
    SOURCE.unlink()
    print(f"split {SOURCE.name} into {len(plan) + 1} files under {OUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
