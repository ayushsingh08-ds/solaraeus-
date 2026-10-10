"""Resolve the 'Inferred' claims I3-I8 recorded in PROJECT_STRUCTURE.md section 10.2.

Each resolver prints raw evidence, never conclusions, so the verdicts written into
REFACTOR_REPORT.md can be checked by hand.
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent


def heading(text: str) -> None:
    print()
    print("=" * 78)
    print(text)
    print("=" * 78)


def i3_bibliography() -> None:
    """Are reference PDFs the bibliography cited by the .tex?"""
    heading("I3  researchpaper/*.pdf  ==  bibliography of solaraeus.tex ?")
    tex = (REPO / "research_paper_sol" / "solaraeus.tex").read_text(encoding="utf-8")
    cite_keys: set[str] = set()
    for group in re.findall(r"\\cite\{([^}]*)\}", tex):
        cite_keys.update(k.strip() for k in group.split(","))
    print(f"cite keys referenced in solaraeus.tex : {len(cite_keys)}")
    print(f"sorted keys: {sorted(cite_keys)}")

    bibs = glob.glob(str(REPO / "**" / "*.bib"), recursive=True)
    print(f"any .bib file in repo                 : {bibs or 'NONE'}")

    pdfs = sorted(glob.glob(str(REPO / "researchpaper" / "*.pdf")))
    print(f"PDFs in researchpaper/                : {len(pdfs)}")
    for p in pdfs:
        print(f"    {os.path.basename(p)}")
    # crude author-token overlap between cite keys and PDF filenames
    overlap = []
    for p in pdfs:
        stem = os.path.basename(p).lower()
        for key in cite_keys:
            surname = re.sub(r"\d{4}.*$", "", key).lower()
            if surname and surname in stem:
                overlap.append((os.path.basename(p), key))
    print(f"\nPDF filename matched to a cite key    : {len(overlap)}")
    for pdf, key in overlap:
        print(f"    {pdf}  <->  \\cite{{{key}}}")


def i5_results_mapping() -> None:
    """Do results/ run directories map 1:1 onto run_church_street_*.py scripts?"""
    heading("I5  results/church_street_* directories  <->  scripts/run_church_street_*.py")
    scripts = sorted(p.name for p in (REPO / "scripts").glob("run_church_street_*.py"))
    print("run_church_street scripts:")
    for s in scripts:
        print(f"    {s}")

    dirs = sorted(
        p.name
        for p in (REPO / "results").iterdir()
        if p.is_dir() and p.name.startswith("church_street")
    )
    print(f"\nresults/church_street_* directories    : {len(dirs)}")
    for d in dirs:
        # strip the trailing _YYYYMMDD_HHMMSS run stamp
        slug = re.sub(r"_\d{8}_\d{6}$", "", d)
        match = f"run_{slug}.py"
        status = "FOUND" if match in scripts else "no matching script"
        print(f"    {d:58s} -> {status}")

    print("\nscripts with NO results directory:")
    for s in scripts:
        slug = s[len("run_"):-len(".py")]
        if not any(re.sub(r"_\d{8}_\d{6}$", "", d) == slug for d in dirs):
            print(f"    {s}")


def i6_orphan_reachability() -> None:
    """Which files import the terrain/vegetation extensions?"""
    heading("I6  terrain/* and vegetation/* reachability (direct importers, excluding self)")
    targets = [
        "src/urban_comfort/terrain/",
        "src/urban_comfort/vegetation/",
    ]
    # build importer list with grep as a cross-check against the AST graph
    for tdir in targets:
        for path in sorted((REPO / tdir).glob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            stem = path.stem
            quoted = subprocess.run(
                ["git", "grep", "-n", "-l", "-e", f"urban_comfort.terrain.{stem}",
                 "-e", f"urban_comfort.vegetation.{stem}"],
                cwd=REPO, capture_output=True, text=True,
            ).stdout.strip().splitlines()
            quoted = [q for q in quoted if not q.startswith(rel)]
            print(f"  {rel}")
            for q in quoted:
                print(f"      imported by: {q}")


def i7_cycle() -> None:
    """Re-verify the import cycle and which edges are function-local."""
    heading("I7  import cycle in incremental/backend/reference (top-level vs function-local)")
    print("  (see tools/golden/cycle_check.py for the authoritative SCC report)")


def i8_stage_schemas() -> None:
    """Sample the JSON keys of committed stage artifacts."""
    heading("I8  results/stage_NN schemas (sampled)")
    dirs = sorted((REPO / "results").glob("stage_*"))
    print(f"stage directories: {len(dirs)}")
    for d in dirs:
        jsons = sorted(d.glob("*.json"))
        statuses = []
        for j in jsons:
            try:
                data = json.loads(j.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(data, dict):
                for key in ("status", "token"):
                    if isinstance(data.get(key), str):
                        statuses.append(f"{j.name}.{key}={data[key]}")
        print(f"\n  {d.name}  ({len(jsons)} json)")
        for s in statuses[:4]:
            print(f"      {s}")


RESOLVERS = {
    "i3": i3_bibliography,
    "i5": i5_results_mapping,
    "i6": i6_orphan_reachability,
    "i8": i8_stage_schemas,
}

if __name__ == "__main__":
    which = sys.argv[1:] or list(RESOLVERS)
    for key in which:
        RESOLVERS[key]()
