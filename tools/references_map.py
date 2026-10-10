"""Regenerate ``references/bibliography-map.md`` from the paper and the PDFs.

Why this exists
---------------
``paper/solaraeus.tex`` cites 26 keys but the repository ships **no ``.bib``
file**, so key -> PDF links were never recorded. Rather than invent
bibliographic data, this script reports the gap honestly: it lists every cite
key, every PDF, and the (weak) filename matches it can find, then asks a human
to resolve the rest.

Usage
-----
    python tools/references_map.py            # write references/bibliography-map.md
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEX = REPO_ROOT / "paper" / "solaraeus.tex"
PDF_DIR = REPO_ROOT / "references" / "pdfs"
OUT = REPO_ROOT / "references" / "bibliography-map.md"

CITE_RE = re.compile(r"\\cite\{([^}]*)\}")
YEAR_RE = re.compile(r"(\d{4})")
# A BibTeX-ish key starts with the (possibly multi-part) surname, then the year:
# ``krayenhoff2014multi`` -> surname ``krayenhoff``, year ``2014``.
SURNAME_RE = re.compile(r"^([A-Za-z]+)")


def cite_keys() -> list[str]:
    """Return every distinct cite key used in the paper, sorted."""
    text = TEX.read_text(encoding="utf-8", errors="replace")
    keys = {k.strip() for group in CITE_RE.findall(text) for k in group.split(",")}
    return sorted(k for k in keys if k)


def surnames_and_years(key: str) -> tuple[str, str]:
    """Split a BibTeX-ish key like ``krayenhoff2014multi`` into (surname, year)."""
    year = YEAR_RE.search(key)
    surname = SURNAME_RE.match(key)
    return (surname.group(1).lower() if surname else ""), (year.group(1) if year else "")


def build_map() -> str:
    """Render the markdown map."""
    keys = cite_keys()
    pdfs = sorted(p.name for p in PDF_DIR.glob("*.pdf"))

    lines = [
        "# Cite key -> reference PDF map",
        "",
        "**STATUS: INCOMPLETE - needs a human.** Regenerate with",
        "`python tools/references_map.py`. The repository contains no `.bib`",
        "file, so any key marked UNMAPPED was never linked to a PDF and is not",
        "guessed at here.",
        "",
        f"- cite keys in `paper/solaraeus.tex`: **{len(keys)}**",
        f"- PDFs in `references/pdfs/`: **{len(pdfs)}**",
        "",
        "## Cite keys",
        "",
        "| # | cite key | PDF in `references/pdfs/` |",
        "|---:|---|---|",
    ]

    mapped: set[str] = set()
    for index, key in enumerate(keys, 1):
        surname, year = surnames_and_years(key)
        hits = [p for p in pdfs if surname and surname in p.lower()]
        exact = [h for h in hits if year and year in h]
        if exact:
            mapped.update(exact)
            where = ", ".join(f"`{h}` (name match, year agrees)" for h in exact)
        elif hits:
            mapped.update(hits)
            where = ", ".join(f"`{h}` (WEAK: name matches, year differs)" for h in hits)
        else:
            where = "UNMAPPED"
        lines.append(f"| {index} | `{key}` | {where} |")

    lines += ["", "## PDFs not linked to any cite key", "", "| # | PDF |", "|---:|---|"]
    for index, pdf in enumerate(pdfs, 1):
        if pdf not in mapped:
            lines.append(f"| {index} | `{pdf}` |")

    lines += [
        "",
        "## What a human must do",
        "",
        "1. Decide whether these PDFs belong in git, in Git LFS, or outside the",
        "   repository behind a download record.",
        "2. Supply `references/references.bib` (26 entries). It cannot be",
        "   reconstructed from the repository without inventing bibliographic data.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    """Write the map and report how complete it is."""
    text = build_map()
    OUT.write_text(text, encoding="utf-8")
    unmapped = text.count("UNMAPPED")
    weak = text.count("WEAK:")
    print(f"wrote {OUT.relative_to(REPO_ROOT)}: {unmapped} unmapped keys, {weak} weak matches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
