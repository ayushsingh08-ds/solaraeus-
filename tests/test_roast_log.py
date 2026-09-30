"""Tests for the Idea Roast Council: the seat definitions and the ruling log.

Two jobs. First, prove the council is wired the way it claims — four seats, three of
them read-only, one Judge that can write, fired in order by a single command. Second,
stop a malformed ruling from being written: the index, the frontmatter, and the Judge's
own section must agree, or the suite fails.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.roast_index import (
    INDEX_BEGIN,
    INDEX_END,
    RULING_FILENAME_RE,
    VERDICTS,
    RoastLogError,
    check_index,
    discover_rulings,
    find_problems,
    load_ruling,
    main,
    parse_frontmatter,
    render_index,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ROASTS_DIR = REPO_ROOT / "roasts"
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"

SEATS = ("believer", "skeptic", "investor", "judge")


def ruling_text(
    *,
    ruling_id: str = "001",
    slug: str = "test-idea",
    verdict: str = "FIX FIRST",
    risk: str = "Nobody has agreed to pay for it.",
    open_questions: int = 1,
    bullet_count: int | None = None,
) -> str:
    """Build a valid ruling document, with knobs to break one thing at a time."""
    listed = open_questions if bullet_count is None else bullet_count
    bullets = "".join(f"- Loose end {index + 1}.\n" for index in range(listed))
    flip = "**Flips to BUILD if:** One buyer signs a paid pilot.\n\n" if verdict == "FIX FIRST" else ""
    return (
        "---\n"
        f'id: "{ruling_id}"\n'
        f"slug: {slug}\n"
        "idea: A test idea with no market.\n"
        "date: 2026-09-30\n"
        f"verdict: {verdict}\n"
        f"biggest_risk: {risk}\n"
        f"open_questions: {open_questions}\n"
        "---\n\n"
        f"# {ruling_id} — A test idea\n\n"
        "## Believer\n\nIt could be great.\n\n"
        "## Skeptic\n\nIt probably will not be.\n\n"
        "## Investor\n\nNo.\n\n"
        "## Judge\n\n"
        f"**VERDICT:** {verdict}\n\n"
        f"**Biggest risk:** {risk}\n\n"
        "**10-minute test:** Ask one buyer for money.\n\n"
        f"{flip}"
        "**Open questions carried forward:**\n\n"
        f"{bullets or '- Nothing outstanding.\n'}"
    )


def write_ruling(directory: Path, text: str, name: str = "001-test-idea.md") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


def index_with(rows: list[list[str]]) -> str:
    table = "\n".join("| " + " | ".join(row) + " |" for row in rows)
    return f"# Ruling Index\n\n{INDEX_BEGIN}\n\n{table}\n\n{INDEX_END}\n"


# --- the council is wired the way it claims -------------------------------------


@pytest.mark.parametrize("seat", SEATS)
def test_every_seat_is_defined(seat: str) -> None:
    path = AGENTS_DIR / f"{seat}.md"
    assert path.exists(), f"council seat {seat!r} is missing from {AGENTS_DIR}"
    fields = parse_frontmatter(path.read_text(encoding="utf-8"), path)
    assert fields.get("name") == seat
    assert fields.get("description"), f"{seat} needs a description so Claude can route to it"
    assert fields.get("tools"), f"{seat} must declare its tool list"


def test_seat_names_are_unique() -> None:
    names = []
    for path in sorted(AGENTS_DIR.glob("*.md")):
        names.append(parse_frontmatter(path.read_text(encoding="utf-8"), path).get("name"))
    assert len(names) == len(set(names)), f"duplicate subagent names silently drop a seat: {names}"


@pytest.mark.parametrize("seat", ("believer", "skeptic", "investor"))
def test_arguing_seats_are_read_only(seat: str) -> None:
    path = AGENTS_DIR / f"{seat}.md"
    tools = {
        tool.strip()
        for tool in parse_frontmatter(path.read_text(encoding="utf-8"), path)["tools"].split(",")
    }
    assert not tools & {"Write", "Edit", "NotebookEdit"}, (
        f"{seat} must not be able to write; the Judge is the only seat that persists anything"
    )


def test_judge_is_the_only_seat_that_can_write() -> None:
    path = AGENTS_DIR / "judge.md"
    fields = parse_frontmatter(path.read_text(encoding="utf-8"), path)
    tools = {tool.strip() for tool in fields["tools"].split(",")}
    assert {"Read", "Write", "Edit"} <= tools
    assert "model" not in fields, "the Judge inherits the session model on purpose"


def test_roast_command_fires_the_seats_in_order() -> None:
    path = COMMANDS_DIR / "roast.md"
    text = path.read_text(encoding="utf-8")
    fields = parse_frontmatter(text, path)
    assert fields.get("description")
    assert fields.get("argument-hint"), "/roast should advertise what to pass it"
    assert "context: fork" not in text.lower(), (
        "a forked context cannot spawn the subagents the command orchestrates"
    )

    positions = [text.find(f"`{seat}`") for seat in SEATS]
    assert all(position != -1 for position in positions), "every seat must be named in /roast"
    assert positions == sorted(positions), "the Judge must be invoked last, after the three seats"


def test_recall_command_only_reads() -> None:
    path = COMMANDS_DIR / "roast-recall.md"
    fields = parse_frontmatter(path.read_text(encoding="utf-8"), path)
    tools = {tool.strip() for tool in fields.get("allowed-tools", "").split(",") if tool.strip()}
    assert not tools & {"Write", "Edit"}, "recall must not modify the council's memory"


# --- the ruling log in this repo is valid and in sync ---------------------------


def test_repo_index_matches_the_rulings() -> None:
    assert find_problems(ROASTS_DIR) == []


def test_rulings_are_discoverable_and_sequentially_numbered() -> None:
    rulings = discover_rulings(ROASTS_DIR)
    assert rulings, "the council should have handed down at least one ruling"
    assert [ruling.id for ruling in rulings] == [f"{index:03d}" for index in range(1, len(rulings) + 1)]


def test_every_ruling_states_a_real_verdict() -> None:
    for ruling in discover_rulings(ROASTS_DIR):
        assert ruling.verdict in VERDICTS
        assert ruling.biggest_risk.strip()
        assert ruling.idea.strip()


def test_roast_index_covers_every_ruling_file() -> None:
    on_disk = {path.name for path in ROASTS_DIR.glob("*.md") if RULING_FILENAME_RE.match(path.name)}
    assert on_disk, "no ruling files found"
    index_text = (ROASTS_DIR / "INDEX.md").read_text(encoding="utf-8")
    for name in sorted(on_disk):
        assert name in index_text, f"{name} is missing from INDEX.md"


# --- a malformed ruling is rejected ---------------------------------------------


def test_frontmatter_rejects_multi_line_values(tmp_path: Path) -> None:
    path = write_ruling(tmp_path, "---\nid: \"001\"\nslug: test-idea\nidea: broken\nhere\n---\n")
    with pytest.raises(RoastLogError, match="key: value"):
        parse_frontmatter(path.read_text(encoding="utf-8"), path)


def test_ruling_rejects_an_unknown_verdict(tmp_path: Path) -> None:
    path = write_ruling(tmp_path, ruling_text(verdict="MAYBE"))
    with pytest.raises(RoastLogError, match="verdict"):
        load_ruling(path)


def test_ruling_rejects_a_verdict_the_judge_contradicts(tmp_path: Path) -> None:
    text = ruling_text(verdict="KILL").replace("**VERDICT:** KILL", "**VERDICT:** BUILD")
    path = write_ruling(tmp_path, text)
    with pytest.raises(RoastLogError, match="Judge section says VERDICT"):
        load_ruling(path)


def test_ruling_rejects_seats_out_of_order(tmp_path: Path) -> None:
    text = ruling_text().replace("## Skeptic", "## Investor").replace(
        "## Investor\n\nNo.", "## Skeptic\n\nNo."
    )
    path = write_ruling(tmp_path, text)
    with pytest.raises(RoastLogError, match="out of order"):
        load_ruling(path)


def test_ruling_rejects_a_missing_flip_condition(tmp_path: Path) -> None:
    text = ruling_text(verdict="FIX FIRST").replace("**Flips to BUILD if:**", "**Notes:**")
    path = write_ruling(tmp_path, text)
    with pytest.raises(RoastLogError, match="Flips to BUILD"):
        load_ruling(path)


def test_ruling_rejects_an_open_question_count_mismatch(tmp_path: Path) -> None:
    path = write_ruling(tmp_path, ruling_text(open_questions=3, bullet_count=1))
    with pytest.raises(RoastLogError, match="open_questions"):
        load_ruling(path)


def test_ruling_rejects_a_missing_open_question_list(tmp_path: Path) -> None:
    text = ruling_text().replace("**Open questions carried forward:**", "**Still wondering:**")
    path = write_ruling(tmp_path, text)
    with pytest.raises(RoastLogError, match="Open questions carried forward"):
        load_ruling(path)


def test_ruling_rejects_a_pipe_in_the_risk(tmp_path: Path) -> None:
    path = write_ruling(tmp_path, ruling_text(risk="Two risks | and a table break."))
    with pytest.raises(RoastLogError, match="breaks the index table"):
        load_ruling(path)


def test_ruling_rejects_a_filename_that_contradicts_frontmatter(tmp_path: Path) -> None:
    path = write_ruling(tmp_path, ruling_text(slug="other-idea"), name="001-test-idea.md")
    with pytest.raises(RoastLogError, match="slug"):
        load_ruling(path)


def test_discovery_rejects_duplicate_ids(tmp_path: Path) -> None:
    write_ruling(tmp_path, ruling_text(slug="first-idea"), name="001-first-idea.md")
    write_ruling(tmp_path, ruling_text(slug="second-idea"), name="001-second-idea.md")
    with pytest.raises(RoastLogError, match="already used"):
        discover_rulings(tmp_path)


# --- the index is regenerated, not hand-faked -----------------------------------


def test_check_index_reports_drift(tmp_path: Path) -> None:
    ruling = load_ruling(write_ruling(tmp_path, ruling_text()))
    stale = index_with([["001", "Some other idea", "2026-09-30", "BUILD", "None", "0", ruling.link]])
    problems = check_index([ruling], stale, tmp_path / "INDEX.md")
    assert any("Idea" in problem for problem in problems)
    assert any("Verdict" in problem for problem in problems)


def test_check_index_reports_a_missing_row(tmp_path: Path) -> None:
    ruling = load_ruling(write_ruling(tmp_path, ruling_text()))
    problems = check_index([ruling], index_with([]), tmp_path / "INDEX.md")
    assert problems and "0 row(s)" in problems[0]


def test_check_index_is_quiet_when_in_sync(tmp_path: Path) -> None:
    ruling = load_ruling(write_ruling(tmp_path, ruling_text()))
    assert check_index([ruling], index_with([ruling.index_row()]), tmp_path / "INDEX.md") == []


def test_check_index_requires_the_markers(tmp_path: Path) -> None:
    with pytest.raises(RoastLogError, match="markers"):
        check_index([], "# Ruling Index\n", tmp_path / "INDEX.md")


def test_render_index_regenerates_the_table_and_keeps_the_prose(tmp_path: Path) -> None:
    first = load_ruling(write_ruling(tmp_path, ruling_text()))
    rendered = render_index(
        f"{INDEX_BEGIN}\n\nstale table\n\n{INDEX_END}\n\nhand-written note\n", [first]
    )
    assert "stale table" not in rendered
    assert "hand-written note" in rendered
    assert first.index_row()[1] in rendered


def test_render_index_creates_a_file_from_scratch() -> None:
    rendered = render_index(None, [])
    assert rendered.startswith("# Ruling Index")
    assert INDEX_BEGIN in rendered and INDEX_END in rendered


# --- the CLI contract that /roast branches on -----------------------------------


def test_cli_check_returns_zero_when_in_sync(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ruling = load_ruling(write_ruling(tmp_path, ruling_text()))
    (tmp_path / "INDEX.md").write_text(index_with([ruling.index_row()]), encoding="utf-8")
    assert main(["--check", "--roasts-dir", str(tmp_path)]) == 0
    assert "agree" in capsys.readouterr().out


def test_cli_check_returns_one_on_drift(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_ruling(tmp_path, ruling_text())
    (tmp_path / "INDEX.md").write_text(index_with([]), encoding="utf-8")
    assert main(["--check", "--roasts-dir", str(tmp_path)]) == 1
    assert "row(s)" in capsys.readouterr().err


def test_cli_check_returns_one_when_the_index_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_ruling(tmp_path, ruling_text())
    assert main(["--check", "--roasts-dir", str(tmp_path)]) == 1
    assert "does not exist" in capsys.readouterr().err


def test_cli_check_returns_two_on_a_malformed_ruling(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_ruling(tmp_path, ruling_text(verdict="MAYBE"))
    assert main(["--check", "--roasts-dir", str(tmp_path)]) == 2
    assert "verdict" in capsys.readouterr().err


def test_cli_write_mode_regenerates_the_table(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ruling = load_ruling(write_ruling(tmp_path, ruling_text()))
    assert main(["--roasts-dir", str(tmp_path)]) == 0
    assert ruling.link in (tmp_path / "INDEX.md").read_text(encoding="utf-8")
    assert "wrote" in capsys.readouterr().out


def test_repo_paths_do_not_depend_on_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert REPO_ROOT.is_dir()
    assert find_problems(ROASTS_DIR) == []
