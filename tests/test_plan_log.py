"""Tests for the planning tournament: the planner definitions and the tournament record.

Two jobs. Prove the tournament is wired the way it claims — four generalist planners who
can research and write, an arbiter that decides, one command that fires them — and stop a
malformed record from being written: a plan with no strategy family, a sourcing ledger row
with neither a URL nor an `unverified` tag, a score table whose arithmetic does not add up,
a trail that skips a round, or a plan marked eliminated in one place and competing in another.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.plan_index import (
    INDEX_BEGIN,
    INDEX_END,
    MAX_TOTAL,
    PLANNER_NAMES,
    RUBRIC,
    PlanLogError,
    check_final_plan,
    check_scores,
    check_trail,
    discover_rounds,
    find_problems,
    load_plan,
    parse_ledger,
    parse_scores,
    render_index,
    weighted_total,
)
from scripts.roast_index import parse_frontmatter

REPO_ROOT = Path(__file__).resolve().parents[1]
PLANS_DIR = REPO_ROOT / "plans"
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"

PLANNERS = PLANNER_NAMES
ARBITER = "planner-arbiter"


# --- fixtures -------------------------------------------------------------------


def make_plan_text(
    *,
    planner: str = "planner-a",
    round_number: int = 1,
    family: str = "gpu-first",
    status: str = "competing",
    thesis: str = "A researched strategy combination, not an opinion.",
    verified: int = 2,
    unverified: int = 1,
) -> str:
    rows = ["| Claim | Source | Accessed |", "| :--- | :--- | :--- |"]
    for index in range(verified):
        rows.append(f"| Verified claim {index + 1}. | https://example.org/source-{index + 1} | 2026-09-30 |")
    for index in range(unverified):
        rows.append(f"| Unverified claim {index + 1}. | unverified | - |")

    sections = [
        ("## Strategy", "The family, the thesis, and what this plan bets on."),
        ("## Architecture", "Kernels, acceleration structure, CPU oracle, GPU-free CI."),
        ("## Attribution", "Components instrumented out of the same solve, summing under test."),
        ("## Interface", "What a practitioner loads, changes, sees, and what is not modelled."),
        ("## Schedule", "Phases with gates and pre-committed fallbacks."),
        ("## Cost claims", "Each claim with its baseline and how it is measured."),
        ("## Paper plan", "Contribution, venue class, evidence table."),
        ("## Cut list", "What is deliberately out of scope, and why that is safe."),
        ("## Sourcing ledger", "\n".join(rows)),
    ]
    body = "\n\n".join(f"{heading}\n\n{text}" for heading, text in sections)
    return (
        "---\n"
        f"planner: {planner}\n"
        f"round: {round_number}\n"
        f"strategy_family: {family}\n"
        f"thesis: {thesis}\n"
        "date: 2026-09-30\n"
        f"status: {status}\n"
        f"sources_verified: {verified}\n"
        f"sources_unverified: {unverified}\n"
        "---\n\n"
        f"# {planner} — round {round_number}\n\n"
        f"{body}\n"
    )


def write_plan(
    root: Path,
    planner: str,
    round_number: int,
    *,
    family: str | None = None,
    status: str = "competing",
) -> Path:
    directory = root / f"r{round_number}"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{planner}.md"
    path.write_text(
        make_plan_text(
            planner=planner,
            round_number=round_number,
            family=family or f"{planner}-family-{round_number}",
            status=status,
        ),
        encoding="utf-8",
    )
    return path


def make_scores(specs: dict[int, list[tuple[str, str, tuple[int, ...], str]]], eliminated: dict[int, tuple[str, str]]) -> str:
    parts = ["# Tournament Scores", "", f"Rubric weights and a total out of {MAX_TOTAL}.", ""]
    for number in sorted(specs):
        parts.append(f"## Round {number}")
        parts.append("")
        parts.append(
            "| Plan | Feasibility | Defensibility | Sourcing | Risk | Interface | Cost | Weighted total | Decision |"
        )
        parts.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for label, planner, axes, decision in specs[number]:
            cells = " | ".join(str(value) for value in axes)
            parts.append(f"| {label} ({planner}) | {cells} | {weighted_total(axes)} | {decision} |")
        parts.append("")
        planner, reason = eliminated[number]
        parts.append(f"**Eliminated:** {planner} — {reason}")
        parts.append("")
    return "\n".join(parts)


CANONICAL_SPECS = {
    1: [
        ("A", "planner-a", (3, 3, 3, 2, 2, 2), "survives"),
        ("B", "planner-b", (3, 2, 3, 3, 2, 2), "survives"),
        ("C", "planner-c", (2, 3, 3, 2, 3, 1), "survives"),
        ("D", "planner-d", (2, 2, 2, 1, 2, 2), "eliminated"),
    ],
    2: [
        ("A", "planner-a", (3, 3, 3, 3, 2, 2), "survives"),
        ("B", "planner-c", (3, 3, 3, 2, 3, 2), "survives"),
        ("C", "planner-b", (2, 3, 3, 2, 2, 2), "eliminated"),
    ],
    3: [
        ("A", "planner-a", (3, 3, 3, 3, 3, 2), "survives"),
        ("B", "planner-c", (3, 3, 3, 2, 3, 3), "eliminated"),
    ],
}
CANONICAL_ELIMINATED = {1: ("planner-d", "weakest sourcing"), 2: ("planner-b", "thinner validation"), 3: ("planner-c", "unmeasured cost claims")}
CANONICAL_STATUS = {
    1: {"planner-a": "competing", "planner-b": "competing", "planner-c": "competing", "planner-d": "eliminated"},
    2: {"planner-a": "competing", "planner-b": "eliminated", "planner-c": "competing"},
    3: {"planner-a": "surviving", "planner-c": "eliminated"},
}


def build_record(root: Path, *, specs=None, eliminated=None, status=None, write_scores: bool = True, write_plan_md: bool = True) -> None:
    specs = specs or CANONICAL_SPECS
    eliminated = eliminated or CANONICAL_ELIMINATED
    status = status or CANONICAL_STATUS
    for number, plans in status.items():
        for planner, state in plans.items():
            write_plan(root, planner, number, status=state)
    if write_scores:
        (root / "SCORES.md").write_text(make_scores(specs, eliminated), encoding="utf-8")
    if write_plan_md and any(state == "surviving" for plans in status.values() for state in plans.values()):
        family = "planner-a-family-3"
        sections = ["## Strategy", "## Architecture", "## Attribution", "## Interface", "## Schedule", "## Cost claims", "## Paper plan", "## Cut list", "## Rejected alternatives"]
        body = "\n\n".join(f"{section}\n\nEnough detail to survive review, in a paragraph that is not empty." for section in sections)
        (root / "PLAN.md").write_text(
            f"# PLAN\n\nThe surviving family is {family} and here is why.\n\n{body}\n\n"
            "## Red team\n\n"
            "- planner-b: the validation plan leans on inter-model comparison where a field check would settle it.\n"
            "- planner-c: the interface latency target is unproven until the kernel exists.\n"
            "- planner-d: the height audit covers twenty buildings, not the precinct.\n",
            encoding="utf-8",
        )


# --- the tournament is wired the way it claims ----------------------------------


@pytest.mark.parametrize("agent", (*PLANNERS, ARBITER))
def test_every_tournament_agent_is_defined(agent: str) -> None:
    path = AGENTS_DIR / f"{agent}.md"
    assert path.exists(), f"missing {path}"
    fields = parse_frontmatter(path.read_text(encoding="utf-8"), path)
    assert fields.get("name") == agent
    assert fields.get("description"), f"{agent} needs a description so Claude can route to it"
    assert fields.get("tools"), f"{agent} must declare its tool list"


def test_agent_names_are_unique() -> None:
    names = [
        parse_frontmatter(path.read_text(encoding="utf-8"), path).get("name")
        for path in sorted(AGENTS_DIR.glob("*.md"))
    ]
    assert len(names) == len(set(names)), f"duplicate subagent names silently drop a seat: {names}"


@pytest.mark.parametrize("planner", PLANNERS)
def test_planners_can_research_and_write_their_own_plan(planner: str) -> None:
    path = AGENTS_DIR / f"{planner}.md"
    tools = {
        tool.strip()
        for tool in parse_frontmatter(path.read_text(encoding="utf-8"), path)["tools"].split(",")
    }
    assert {"WebSearch", "WebFetch"} <= tools, f"{planner} must be able to research before it plans"
    assert {"Write", "Read"} <= tools, f"{planner} must be able to read evidence and write its plan"
    assert "unverified" in path.read_text(encoding="utf-8"), (
        f"{planner} must carry the sourcing rule: a claim with no live source is tagged unverified"
    )


def test_planners_own_the_whole_project_not_a_slice(planner: str = "planner-a") -> None:
    text = (AGENTS_DIR / f"{planner}.md").read_text(encoding="utf-8")
    for part in ("GPU", "attribution", "interface", "paper"):
        assert part.lower() in text.lower(), f"{planner} must plan the whole project, including {part}"


def test_arbiter_scores_and_keeps_the_record() -> None:
    text = (AGENTS_DIR / f"{ARBITER}.md").read_text(encoding="utf-8")
    assert "eliminate" in text.lower()
    assert "diversity" in text.lower()
    assert "PLAN.md" in text


def test_plan_command_fires_all_four_planners_without_forking() -> None:
    path = COMMANDS_DIR / "plan.md"
    text = path.read_text(encoding="utf-8")
    fields = parse_frontmatter(text, path)
    assert fields.get("description")
    assert fields.get("argument-hint")
    assert "context: fork" not in text.lower(), "a forked context cannot spawn the planners it orchestrates"
    positions = [text.find(f"`{planner}`") for planner in PLANNERS]
    assert all(position != -1 for position in positions), "every planner must be named in /plan"
    assert ARBITER in text, "the round must be handed to the arbiter"


def test_plan_recall_only_reads() -> None:
    path = COMMANDS_DIR / "plan-recall.md"
    fields = parse_frontmatter(path.read_text(encoding="utf-8"), path)
    tools = {tool.strip() for tool in fields.get("allowed-tools", "").split(",") if tool.strip()}
    assert not tools & {"Write", "Edit"}, "recall must not modify the tournament record"


# --- a malformed plan is rejected -----------------------------------------------


def test_plan_requires_a_strategy_family(tmp_path: Path) -> None:
    path = write_plan(tmp_path, "planner-a", 1, family="Not Kebab Case")
    with pytest.raises(PlanLogError, match="kebab-case"):
        load_plan(path, 1)


def test_plan_round_must_match_its_folder(tmp_path: Path) -> None:
    directory = tmp_path / "r2"
    directory.mkdir()
    path = directory / "planner-a.md"
    path.write_text(make_plan_text(round_number=1), encoding="utf-8")
    with pytest.raises(PlanLogError, match="round"):
        load_plan(path, 2)


def test_plan_rejects_an_unknown_status(tmp_path: Path) -> None:
    directory = tmp_path / "r1"
    directory.mkdir()
    path = directory / "planner-a.md"
    path.write_text(make_plan_text(status="winner"), encoding="utf-8")
    with pytest.raises(PlanLogError, match="status"):
        load_plan(path, 1)


def test_plan_rejects_a_missing_section(tmp_path: Path) -> None:
    directory = tmp_path / "r1"
    directory.mkdir()
    path = directory / "planner-a.md"
    text = make_plan_text().replace("## Cut list", "## Nice to have")
    path.write_text(text, encoding="utf-8")
    with pytest.raises(PlanLogError, match="Cut list"):
        load_plan(path, 1)


def test_plan_rejects_sections_out_of_order(tmp_path: Path) -> None:
    directory = tmp_path / "r1"
    directory.mkdir()
    path = directory / "planner-a.md"
    text = (
        make_plan_text()
        .replace("## Attribution", "## Placeholder")
        .replace("## Interface", "## Attribution")
        .replace("## Placeholder", "## Interface")
    )
    path.write_text(text, encoding="utf-8")
    with pytest.raises(PlanLogError, match="out of order"):
        load_plan(path, 1)


# --- the sourcing ledger is the honesty mechanism -------------------------------


def test_ledger_rejects_a_claim_with_no_url_and_no_unverified_tag(tmp_path: Path) -> None:
    text = make_plan_text().replace(
        "| Verified claim 1. | https://example.org/source-1 | 2026-09-30 |",
        "| Speedup of 40x over ENVI-met. | a blog post I remember | 2026-09-30 |",
    )
    with pytest.raises(PlanLogError, match="neither a URL nor"):
        parse_ledger(text, tmp_path / "planner-a.md")


def test_ledger_requires_an_access_date(tmp_path: Path) -> None:
    text = make_plan_text().replace(
        "| Verified claim 1. | https://example.org/source-1 | 2026-09-30 |",
        "| A claim. | https://example.org/source-1 | recently |",
    )
    with pytest.raises(PlanLogError, match="access date"):
        parse_ledger(text, tmp_path / "planner-a.md")


def test_ledger_counts_must_match_the_frontmatter(tmp_path: Path) -> None:
    directory = tmp_path / "r1"
    directory.mkdir()
    path = directory / "planner-a.md"
    path.write_text(make_plan_text(verified=3, unverified=0).replace("sources_verified: 3", "sources_verified: 2"), encoding="utf-8")
    with pytest.raises(PlanLogError, match="sources_verified"):
        load_plan(path, 1)


def test_ledger_accepts_honest_unverified_rows(tmp_path: Path) -> None:
    verified, unverified = parse_ledger(make_plan_text(verified=1, unverified=2), tmp_path / "planner-a.md")
    assert (verified, unverified) == (1, 2)


# --- the trail is a trail -------------------------------------------------------


def test_round_one_must_run_every_planner(tmp_path: Path) -> None:
    write_plan(tmp_path, "planner-a", 1)
    problems = check_trail(discover_rounds(tmp_path))
    assert any("round one must run all" in problem for problem in problems)


def test_rounds_must_be_contiguous(tmp_path: Path) -> None:
    build_record(tmp_path)
    (tmp_path / "r2").rename(tmp_path / "r4")
    for path in (tmp_path / "r4").glob("*.md"):
        path.write_text(path.read_text(encoding="utf-8").replace("round: 2", "round: 4"), encoding="utf-8")
    problems = check_trail(discover_rounds(tmp_path))
    assert any("contiguous" in problem for problem in problems)


def test_competitors_must_be_the_survivors_of_the_previous_round(tmp_path: Path) -> None:
    build_record(tmp_path)
    (tmp_path / "r2" / "planner-d.md").write_text(
        make_plan_text(planner="planner-d", round_number=2, status="competing"), encoding="utf-8"
    )
    problems = check_trail(discover_rounds(tmp_path))
    assert any("survivors of r1" in problem or "after a round of" in problem for problem in problems)


def test_duplicate_strategy_families_are_rejected(tmp_path: Path) -> None:
    build_record(tmp_path)
    (tmp_path / "r1" / "planner-b.md").write_text(
        make_plan_text(planner="planner-b", round_number=1, family="planner-a-family-1"), encoding="utf-8"
    )
    problems = check_trail(discover_rounds(tmp_path))
    assert any("not diverse" in problem for problem in problems)


def test_a_completed_round_must_eliminate_exactly_one_plan(tmp_path: Path) -> None:
    build_record(tmp_path, status={1: {planner: "competing" for planner in PLANNERS}, 2: {"planner-a": "competing", "planner-b": "competing", "planner-c": "competing"}, 3: {"planner-a": "surviving", "planner-c": "eliminated"}})
    problems = check_trail(discover_rounds(tmp_path))
    assert any("exactly one plan" in problem for problem in problems)


def test_a_survivor_may_only_exist_in_the_last_round(tmp_path: Path) -> None:
    build_record(tmp_path, status={1: {"planner-a": "surviving", "planner-b": "competing", "planner-c": "competing", "planner-d": "eliminated"}, 2: CANONICAL_STATUS[2], 3: CANONICAL_STATUS[3]})
    problems = check_trail(discover_rounds(tmp_path))
    assert any("not the last round" in problem for problem in problems)


def test_last_round_must_name_a_survivor_when_it_eliminates(tmp_path: Path) -> None:
    build_record(tmp_path, status={1: CANONICAL_STATUS[1], 2: CANONICAL_STATUS[2], 3: {"planner-a": "competing", "planner-c": "eliminated"}})
    problems = check_trail(discover_rounds(tmp_path))
    assert any("nothing is marked surviving" in problem for problem in problems)


# --- scores ---------------------------------------------------------------------


def test_score_arithmetic_must_match_the_weights(tmp_path: Path) -> None:
    build_record(tmp_path)
    text = (tmp_path / "SCORES.md").read_text(encoding="utf-8")
    broken = text.replace(f"| {weighted_total((3, 3, 3, 2, 2, 2))} | survives |", f"| {MAX_TOTAL} | survives |", 1)
    problems = check_scores(discover_rounds(tmp_path), broken, tmp_path / "SCORES.md")
    assert any("weigh to" in problem for problem in problems)


def test_each_round_marks_exactly_one_elimination(tmp_path: Path) -> None:
    build_record(tmp_path)
    text = (tmp_path / "SCORES.md").read_text(encoding="utf-8").replace("| eliminated |", "| survives |", 1)
    problems = check_scores(discover_rounds(tmp_path), text, tmp_path / "SCORES.md")
    assert any("expected one" in problem for problem in problems)


def test_elimination_needs_a_written_justification(tmp_path: Path) -> None:
    build_record(tmp_path)
    text = (tmp_path / "SCORES.md").read_text(encoding="utf-8").replace("**Eliminated:**", "**Removed:**")
    problems = check_scores(discover_rounds(tmp_path), text, tmp_path / "SCORES.md")
    assert any("written justification" in problem for problem in problems)


def test_elimination_must_match_the_plan_frontmatter(tmp_path: Path) -> None:
    build_record(tmp_path)
    text = (tmp_path / "SCORES.md").read_text(encoding="utf-8").replace("**Eliminated:** planner-d", "**Eliminated:** planner-a", 1)
    problems = check_scores(discover_rounds(tmp_path), text, tmp_path / "SCORES.md")
    assert any("justification names" in problem or "but" in problem for problem in problems)


def test_a_round_with_no_score_table_is_reported(tmp_path: Path) -> None:
    build_record(tmp_path)
    text = (tmp_path / "SCORES.md").read_text(encoding="utf-8")
    problems = check_scores(discover_rounds(tmp_path), text.split("## Round 3")[0], tmp_path / "SCORES.md")
    assert any("round 3 has no score table" in problem for problem in problems)


def test_parse_scores_reads_every_round(tmp_path: Path) -> None:
    build_record(tmp_path)
    parsed = parse_scores((tmp_path / "SCORES.md").read_text(encoding="utf-8"), tmp_path / "SCORES.md")
    assert sorted(parsed) == [1, 2, 3]
    assert parsed[1][0].axes == (3, 3, 3, 2, 2, 2)
    assert sum(1 for row in parsed[1] if row.decision == "eliminated") == 1


# --- the final plan -------------------------------------------------------------


def test_final_plan_is_required_once_a_survivor_exists(tmp_path: Path) -> None:
    build_record(tmp_path, write_plan_md=False)
    problems = check_final_plan(discover_rounds(tmp_path), tmp_path)
    assert any("PLAN.md does not exist" in problem for problem in problems)


def test_final_plan_must_name_the_winning_family(tmp_path: Path) -> None:
    build_record(tmp_path)
    path = tmp_path / "PLAN.md"
    path.write_text(path.read_text(encoding="utf-8").replace("planner-a-family-3", "some-other-family"), encoding="utf-8")
    problems = check_final_plan(discover_rounds(tmp_path), tmp_path)
    assert any("does not name the surviving strategy family" in problem for problem in problems)


def test_final_plan_keeps_the_red_team_section(tmp_path: Path) -> None:
    build_record(tmp_path)
    path = tmp_path / "PLAN.md"
    path.write_text(path.read_text(encoding="utf-8").split("## Red team")[0], encoding="utf-8")
    problems = check_final_plan(discover_rounds(tmp_path), tmp_path)
    assert any("Red team" in problem for problem in problems)


# --- the index ------------------------------------------------------------------


def test_render_index_regenerates_the_table_and_keeps_prose(tmp_path: Path) -> None:
    rows = [["1", "planner-a", "family-a", "A thesis.", "competing", "38", "[r1/planner-a.md](r1/planner-a.md)"]]
    rendered = render_index(f"{INDEX_BEGIN}\n\nstale\n\n{INDEX_END}\n\nhand-written note\n", rows)
    assert "stale" not in rendered
    assert "hand-written note" in rendered
    assert "family-a" in rendered


# --- the record in this repository ----------------------------------------------


def test_repo_record_is_consistent() -> None:
    assert find_problems(PLANS_DIR) == []


def test_repo_tournament_finished_with_one_survivor() -> None:
    rounds = discover_rounds(PLANS_DIR)
    survivors = [plan for plans in rounds.values() for plan in plans if plan.status == "surviving"]
    assert len(survivors) == 1, "the tournament must end with exactly one surviving plan"
    assert len(rounds) <= 3, "the tournament is capped at three rounds"
    assert (PLANS_DIR / "PLAN.md").exists()


def test_repo_index_covers_every_plan() -> None:
    rounds = discover_rounds(PLANS_DIR)
    index_text = (PLANS_DIR / "INDEX.md").read_text(encoding="utf-8")
    for plans in rounds.values():
        for plan in plans:
            assert plan.link in index_text, f"{plan.link} is missing from plans/INDEX.md"


def test_every_plan_did_real_research() -> None:
    for plans in discover_rounds(PLANS_DIR).values():
        for plan in plans:
            assert plan.sources_verified >= 1, f"{plan.path} cites nothing it actually opened"


def test_eliminated_plans_are_preserved() -> None:
    rounds = discover_rounds(PLANS_DIR)
    for number, plans in rounds.items():
        for plan in plans:
            if plan.status == "eliminated":
                assert plan.path.exists(), f"{plan.path} was deleted instead of archived"
                assert plan.sources_verified >= 1, "an archived plan keeps its evidence trail"
