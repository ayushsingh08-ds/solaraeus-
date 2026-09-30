---
description: Run the full Idea Roast Council on an idea — Believer, then Skeptic, then Investor, then Judge rules and saves the verdict.
argument-hint: <the idea in one or two sentences, or a path to a file containing it>
allowed-tools: Read, Grep, Glob, Write, Edit, Agent, Task, Bash
---

Run the Idea Roast Council on the idea in `$ARGUMENTS`.

The council is four seats, each locked to one lens, and **the order is the whole point**. Every seat must argue about the same idea, and each seat must see the arguments of the seats before it. Do not shortcut the sequence and do not write the arguments yourself: delegate each seat to its subagent and pass through what it actually returned.

## Step 1 — Get the idea

- If `$ARGUMENTS` is non-empty, that is the idea. If it names a file path, read the file and use its contents.
- If it is empty, read `roasts/_inbox.md` and take the first idea that has not been ruled on.
- If there is no idea anywhere, ask me for one in a single question and stop.

## Step 2 — Check the council's memory

Read `roasts/INDEX.md`. If this same idea has been ruled on before, read that ruling file too and carry its open questions and its "change that flips it" condition into this run — the council resumes rather than restarts. State the next free three-digit ruling number now.

## Step 3 — Run the seats in order

Delegate with the Agent tool, one seat at a time, waiting for each before starting the next:

1. `believer` — pass the idea text. Capture its case verbatim.
2. `skeptic` — pass the idea text **and** the Believer's full case. Capture its attack verbatim.
3. `investor` — pass the idea text, the Believer's case, **and** the Skeptic's attack. Capture its assessment verbatim.
4. `judge` — pass the idea text, all three arguments above, and the ruling number from Step 2. Tell it to read `roasts/TEMPLATE.md`, write the ruling, update `roasts/INDEX.md`, and update `roasts/_inbox.md`.

## Step 4 — Close the loop

Run `python scripts/roast_index.py --check`. If it reports drift, fix `roasts/INDEX.md` so it matches the rulings exactly.

## Step 5 — Reply

Reply in at most five lines: the verdict, the biggest risk, the 10-minute test, the ruling file path as a clickable link, and the open questions the council is still carrying. Do not paste the four full arguments into the chat — they live in the ruling file.
