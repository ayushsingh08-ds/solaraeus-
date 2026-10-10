# `references/` — third-party literature

This directory holds reference material **by other authors**. No file here is
project output, and nothing in `src/` or `tests/` reads it.

```
references/
├── README.md              <- this file
├── bibliography-map.md    <- cite key -> PDF status (see below)
└── pdfs/                  <- 17 downloaded papers (147 MB)
```

## What these PDFs are (verified, not assumed)

`paper/solaraeus.tex` cites **26 keys**:

```
bauer2020accelerating  brode2012deriving     bruse1998simulating
chatzipoulka2016sky    chen2012gis           fanger1970thermal
fiala2012utci          forrester2008engineering  gal2009sky
grimmond2010climate    jendritzky2012universal   kastner2020ray
krayenhoff2014multi     lindberg2008solweig   lindberg2010spatial
lindberg2018urban      matzarakis2007modelling   moller1997fast
oke1982canyon          parker2010optix       robinson2004sun
sadeghipour2013ladybug steyn1980svf          teller1992visibility
wald2014embree         zhang2019gpu
```

There is **no `.bib` file in the repository**, and the 17 PDFs are named
`author_year.pdf`, which does not line up with the citation keys. Only **2 of
the 17** can be matched to a key with any confidence:

| PDF | Likely key | Confidence |
|---|---|---|
| `chen_2024.pdf` | `chen2012gis` | low — the years disagree (2024 vs 2012) |
| `krayenhoff_2021.pdf` | `krayenhoff2014multi` | low — the years disagree (2021 vs 2014) |

Everything else is unmatched. Because the mapping cannot be established from
the repository alone, **the full table is recorded in
[`bibliography-map.md`](references/bibliography-map.md) and left as a human
decision** rather than guessed at in a generated `.bib`.

## Why they are tracked rather than downloaded on demand

They are the only copy available on this machine; dropping them would lose
content, and the brief for this overhaul forbids deleting evidence. They are
also not downloadable reproducibly (no DOI/URL record exists in the repo).

**Needs human decision:** move to Git LFS, gitignore with a real download
record, or keep as tracked files. See `REFACTOR_REPORT.md` §Needs human
decision.
