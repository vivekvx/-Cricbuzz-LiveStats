"""Exact assignment questions with executable SQLite statements."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPLANATIONS = [
    "Filter the represented country and project player attributes.",
    "Join teams and venues; use a bounded 30-day date window.",
    "Aggregate stored scorecards into career ODI totals and order by runs.",
    "Apply the strict capacity threshold; unknown capacities are excluded.",
    "Left join completed winners so teams with zero wins remain visible.",
    "Group the unique player dimension by role.",
    "Take the maximum innings score per international format.",
    "Use a half-open 2024 start-date interval.",
    "Filter all-rounders and apply both strict career thresholds per format.",
    "Join completed match metadata and return the 20 most recent.",
    "Pivot format totals; overall average is total runs divided by dismissals.",
    "Compare venue and team countries using team appearances; retain zero-win teams and both Home/Away rows. Neutral venues count as away.",
    "Self join adjacent positions in one innings. Combined scores are a proxy, not verified partnerships.",
    "Aggregate spells to match appearances, require 24 legal balls per appearance, then at least three matches per venue.",
    "Apply victory-method-specific margins; aggregate innings to player-match before averaging or counting wins.",
    "Count participant appearances for yearly eligibility and runs-per-match denominator; use the same non-upcoming match set for batting totals. Average strike rates over recorded batting innings.",
    "Measure completed decisive matches with known toss information; exclude ties and no-results from denominator.",
    "Combine ODI, T20I and domestic T20 spells; use six times runs conceded divided by legal balls.",
    "Filter each innings to at least 10 balls since 2022; use population standard deviation.",
    "Count participant appearances separately from batting innings; pivot averages without multiplying match counts.",
    "Compute batting, bowling and fielding components separately, then dense rank within format. Missing components contribute zero; undefined average terms contribute zero.",
    "Qualify canonical team pairs over three years, then report each team at venue/approach grain, with pair-wide win percentages. Run and wicket margins stay separate.",
    "Aggregate Test innings into player-match totals before selecting the latest ten batting matches; compare last-five and last-ten match means, strike rates and consistency. Count individual fifty-plus innings within that window. Thresholds appear in assumptions.",
    "Canonicalize adjacent-position pairs; rank success percentage then average combined runs. Proxy only.",
    "Use participant match appearances over the trailing three years, retain quarters with three matches and players with six such quarters, then compare only adjacent calendar quarters. Show gaps without inventing quarter-on-quarter changes.",
]
ASSUMPTIONS = """Dataset career totals cover stored scorecards only, not necessarily a complete real career.
All divisions guard zero denominators; an undismissed batter has an undefined (NULL) average.
Formats Test, ODI, T20I and domestic T20 remain distinct; Q18 and Q20 explicitly combine T20I/T20.
Q13/Q24 use adjacent batting-position combined-score proxies, never actual partnership runs.
Q17 excludes no-result/tie matches with no winner. Q19 uses population standard deviation and >=10 balls per eligible innings.
Q21 missing disciplines and undefined average terms contribute zero; no 25-point bowling bonus is awarded to non-bowlers.
Q23 Excellent: last5 mean >=50, >=last10 mean, last5 SR >=last10 SR, population SD <=30, >=3 scores >50;
otherwise Good >=35, Average >=20, Poor <20. Fewer than ten batting matches are reported with their count; fifty-plus here means >50 per the source document.
Q25 improving/declining means a change strictly above +5/below -5 runs; otherwise stable.
Career ascending/declining means final minus first qualifying quarter strictly above +10/below -10 runs; otherwise stable.
Q23 averages/stddev use match runs (both Test innings combined); fifty-plus counts still refer to individual innings.
Q25 uses a trailing three-year window ending at :as_of. DNB appearances count as matches with zero runs and undefined strike rate.
Quarter changes across missing/nonqualifying quarters are NULL and explicitly marked as a gap.
Sample date windows use a visible 2026-10-24 reference date; live mode defaults to today's local date.
"""
QUESTIONS = json.loads((ROOT / "docs/questions.json").read_text())
for item, explanation in zip(QUESTIONS, EXPLANATIONS):
    item["sql"] = (ROOT / "analytics/sql" / f"q{item['id']:02}.sql").read_text()
    item["explanation"] = explanation
