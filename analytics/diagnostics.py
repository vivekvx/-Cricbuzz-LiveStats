"""Explain each query's data requirements without changing assignment thresholds."""

import sqlite3
from analytics.queries import execute
from analytics.query_registry import QUESTIONS
from database.connection import read_query

REQUIREMENTS = {
    1: "Player profiles with country represented set to India.",
    2: "Live/completed match dates within the selected last 30 days.",
    3: "Imported ODI batting scorecards; profile career tables are separate.",
    4: "Venue capacity metadata greater than 50,000.",
    5: "Teams and completed matches with recognized winners.",
    6: "Player records with playing roles; Unknown is a separate group.",
    7: "Imported Test, ODI or T20I batting innings.",
    8: "Series metadata with a start date in 2024.",
    9: "Known all-rounders with more than 1,000 runs AND more than 50 wickets in one format's imported scorecards.",
    10: "Completed match records (up to the most recent 20).",
    11: "The same player represented in at least two international formats' scorecards.",
    12: "Completed matches with known team countries and venue countries.",
    13: "Adjacent batting positions whose combined innings scores are at least 100 (proxy only).",
    14: "At least three matches per bowler at a venue, each with at least 24 legal balls.",
    15: "Batting scorecards for wins by fewer than 50 runs or five wickets.",
    16: "At least five recorded match appearances for the same player in one year since 2020.",
    17: "Completed decisive matches with toss winner and bat/bowl decision imported.",
    18: "At least ten ODI/T20I/T20 bowling matches per player and an average of two overs per match.",
    19: "Batting innings since 2022 with at least ten balls faced.",
    20: "At least 20 recorded appearances per player in Test, ODI, T20I or T20.",
    21: "Imported scorecard performances; missing fielding produces only a partial ranking.",
    22: "At least five completed meetings of a team pair in the selected trailing three years.",
    23: "Imported batting matches; fewer than ten matches produce a limited-sample form result.",
    24: "The same adjacent-position batting pair in at least five innings (proxy only).",
    25: "Six qualifying quarters per player in the trailing three years, with at least three appearances per quarter.",
}


def dataset_summary(path):
    return read_query(
        path,
        """SELECT
        (SELECT COUNT(*) FROM matches) listed_matches,
        (SELECT COUNT(DISTINCT match_id) FROM innings) scorecard_matches,
        (SELECT COUNT(*) FROM players) players,
        (SELECT COUNT(*) FROM batting) batting_rows,
        (SELECT COUNT(*) FROM players WHERE role='Unknown') unknown_roles,
        (SELECT COUNT(*) FROM venues WHERE capacity IS NOT NULL) known_capacities,
        (SELECT COUNT(*) FROM series) series_records,
        (SELECT COUNT(*) FROM player_career_stats) career_tables""",
    )[0]


def evidence(path, number, as_of):
    """Use observed counts to explain the two reported failures precisely."""
    if number == 9:
        r = read_query(
            path,
            """SELECT
          (SELECT COUNT(*) FROM players WHERE role='All-rounder') known_allrounders,
          COALESCE(MAX(c.runs),0) max_runs,COALESCE(MAX(c.wickets),0) max_wickets
          FROM career c JOIN players p ON p.id=c.player_id WHERE p.role='All-rounder'""",
        )[0]
        return (
            f"Known all-rounders: {r['known_allrounders']}; highest stored runs per format: {r['max_runs']}; "
            f"highest stored wickets per format: {r['max_wickets']}. "
            "These maxima may belong to different players. Fetched career tables are not included in this scorecard-based query."
        )
    if number == 16:
        r = read_query(
            path,
            """SELECT COALESCE(MAX(n),0) maximum FROM (
          SELECT COUNT(*) n FROM participants a JOIN matches m ON m.id=a.match_id
          WHERE m.match_date>='2020-01-01' AND m.status<>'Upcoming'
          GROUP BY a.player_id,strftime('%Y',m.match_date))""",
        )[0]
        return f"Most recorded appearances by any player in a single eligible year: {r['maximum']}. This question requires at least 5."
    return ""


def empty_explanation(path, number, as_of, mode):
    s = dataset_summary(path)
    prefix = (
        f"Q{number} returned 0 rows. This database has {s['scorecard_matches']} matches with detailed scorecards "
        f"and {s['batting_rows']} batting innings; {s['listed_matches']} listed matches do not necessarily have scorecards. "
    )
    return (
        prefix
        + "Required: "
        + REQUIREMENTS[number]
        + " "
        + evidence(path, number, as_of)
        + (
            " Live imports are incomplete, so this is not evidence that no real player or match qualifies."
            if mode == "Live API"
            else " No sample rows meet these conditions at the selected reference date."
        )
    )


def audit_questions(path, as_of):
    """Run all 25 read-only statements; keep failures distinct from empty results."""
    rows = []
    for q in QUESTIONS:
        try:
            result = execute(path, q["id"], as_of)
            rows.append(
                {
                    "Question": f"Q{q['id']}",
                    "Rows": len(result),
                    "Status": "Has results" if result else "No qualifying rows",
                    "Data needed": REQUIREMENTS[q["id"]],
                }
            )
        except (sqlite3.Error, ValueError) as exc:
            rows.append(
                {
                    "Question": f"Q{q['id']}",
                    "Rows": None,
                    "Status": f"Query failed: {exc}",
                    "Data needed": REQUIREMENTS[q["id"]],
                }
            )
    return rows
