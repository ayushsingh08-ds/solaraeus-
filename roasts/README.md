# roasts/

The Idea Roast Council's memory. Four agents tear an idea apart, a judge rules, and the ruling lands here so the next session continues instead of starting over.

## The council

Four seats, defined in `.claude/agents/`, each locked to a single lens:

| Seat | Job | Tools |
| :--- | :--- | :--- |
| `believer` | The strongest honest case **for** the idea. | read-only |
| `skeptic` | Attacks it, and tries to kill it if it deserves to die. | read-only |
| `investor` | Whether real money shows up, and how fast. Blunt and numeric. | read-only |
| `judge` | Reads all three, rules `BUILD` / `FIX FIRST` / `KILL`, then saves the ruling. | read + write |

The order is the whole point: the Judge rules only after hearing all three, and only the Judge can write. Each seat is given the arguments of the seats before it, so the Investor argues against a real case rather than a straw man.

## Running it

```
/roast <your idea>        # or /roast alone to take the next idea from _inbox.md
/roast-recall <idea>      # what the council already decided, without re-fighting it
```

`/roast` resolves the idea, checks this folder for a prior ruling on it, runs the four seats in order, has the Judge write the ruling and update the index, and verifies the index still matches.

## Files

- `TEMPLATE.md` — the ruling skeleton the Judge copies. Frontmatter is machine-read; the four seat headings must appear in order.
- `INDEX.md` — one row per ruling, between `<!-- index:begin -->` and `<!-- index:end -->` markers.
- `_inbox.md` — ideas awaiting a roast, plus the open questions rulings left behind.
- `NNN-slug.md` — the rulings themselves, numbered from `001`.

## Keeping it honest

`scripts/roast_index.py` owns the index table:

```bash
python scripts/roast_index.py            # regenerate INDEX.md from the rulings
python scripts/roast_index.py --check    # exit 1 if the index has drifted
```

`pytest tests/test_roast_log.py` runs the same checks, so a malformed ruling or a stale index fails the suite rather than quietly rotting. Nothing here is faked at write time: if `--check` passes, the index matches the rulings.

## Rules the council keeps

1. A ruling is never edited to look better. A changed mind is a new ruling that supersedes the old one by number.
2. Unproven claims stay unproven. If the Believer asserts a market and nobody verified it, it is an open question, not a fact.
3. Every ruling ends with a test cheap enough to run today, because a verdict nobody can act on is decoration.

## Adding a seat

Add a Markdown file to `.claude/agents/` with `name`, `description`, `tools`, and (optionally) `model` frontmatter, then slot it into `.claude/commands/roast.md`. Keep each seat to one lens — a seat that hedges is a seat that adds nothing.
