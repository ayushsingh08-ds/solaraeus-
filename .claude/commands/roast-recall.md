---
description: Recall what the council already decided about an idea, and what it was still waiting on, without re-running the roast.
argument-hint: [idea, keyword, or ruling number — leave blank for the full index]
allowed-tools: Read, Grep, Glob
---

Recall the council's ruling on `$ARGUMENTS`.

1. Read `roasts/INDEX.md`. If `$ARGUMENTS` is empty, list every ruling: number, idea, date, verdict, and biggest risk.
2. Otherwise match `$ARGUMENTS` against the ruling numbers, ideas, and keywords in the index, and read the ruling file that matches. If several match, read them all and say which is which.
3. If nothing matches, say so plainly and read `roasts/_inbox.md` to report which ideas are still waiting to be roasted.

Report, briefly:

- the **verdict** and the date it was handed down;
- the **single biggest risk** the Judge identified;
- the **10-minute test** that ruling prescribed, and whether anything in the repo suggests it has been run;
- the **exact change that flips it to BUILD**, if the verdict was FIX FIRST;
- the **open questions** still carried in `roasts/_inbox.md` for that idea.

Do not re-argue the case, do not call the other seats, and do not modify any file — this command only reads the memory the council kept.
