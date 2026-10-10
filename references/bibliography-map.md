# Cite key -> reference PDF map

**STATUS: INCOMPLETE - needs a human.** Regenerate with
`python tools/references_map.py`. The repository contains no `.bib`
file, so any key marked UNMAPPED was never linked to a PDF and is not
guessed at here.

- cite keys in `paper/solaraeus.tex`: **26**
- PDFs in `references/pdfs/`: **17**

## Cite keys

| # | cite key | PDF in `references/pdfs/` |
|---:|---|---|
| 1 | `bauer2020accelerating` | UNMAPPED |
| 2 | `brode2012deriving` | UNMAPPED |
| 3 | `bruse1998simulating` | UNMAPPED |
| 4 | `chatzipoulka2016sky` | UNMAPPED |
| 5 | `chen2012gis` | `chen_2024.pdf` (WEAK: name matches, year differs) |
| 6 | `fanger1970thermal` | UNMAPPED |
| 7 | `fiala2012utci` | UNMAPPED |
| 8 | `forrester2008engineering` | UNMAPPED |
| 9 | `gal2009sky` | UNMAPPED |
| 10 | `grimmond2010climate` | UNMAPPED |
| 11 | `jendritzky2012universal` | UNMAPPED |
| 12 | `kastner2020ray` | UNMAPPED |
| 13 | `krayenhoff2014multi` | `krayenhoff_2021.pdf` (WEAK: name matches, year differs) |
| 14 | `lindberg2008solweig` | UNMAPPED |
| 15 | `lindberg2010spatial` | UNMAPPED |
| 16 | `lindberg2018urban` | UNMAPPED |
| 17 | `matzarakis2007modelling` | UNMAPPED |
| 18 | `moller1997fast` | UNMAPPED |
| 19 | `oke1982canyon` | UNMAPPED |
| 20 | `parker2010optix` | UNMAPPED |
| 21 | `robinson2004sun` | UNMAPPED |
| 22 | `sadeghipour2013ladybug` | UNMAPPED |
| 23 | `steyn1980svf` | UNMAPPED |
| 24 | `teller1992visibility` | UNMAPPED |
| 25 | `wald2014embree` | UNMAPPED |
| 26 | `zhang2019gpu` | UNMAPPED |

## PDFs not linked to any cite key

| # | PDF |
|---:|---|
| 1 | `baia_2026.pdf` |
| 2 | `bourquin_2025.pdf` |
| 4 | `eingrüber_2025.pdf` |
| 5 | `federica_2021.pdf` |
| 6 | `freude_2023.pdf` |
| 7 | `freude_2025.pdf` |
| 8 | `kamath_2026.pdf` |
| 10 | `luo_2022.pdf` |
| 11 | `mei_2025.pdf` |
| 12 | `rayegan_2025.pdf` |
| 13 | `shaoxiang_2024.pdf` |
| 14 | `tao_2025.pdf` |
| 15 | `wenhui_2023.pdf` |
| 16 | `xuan_2020_.pdf` |
| 17 | `yuan_2025.pdf` |

## What a human must do

1. Decide whether these PDFs belong in git, in Git LFS, or outside the
   repository behind a download record.
2. Supply `references/references.bib` (26 entries). It cannot be
   reconstructed from the repository without inventing bibliographic data.
