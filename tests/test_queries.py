"""Independent fixture oracles for every mandatory query."""

import math
import statistics
import pytest
from analytics.queries import execute
from database.seed import DEMO_DATE
from database.connection import connect


def query(db, n):
    return execute(db, n, DEMO_DATE)


def named(rows, name="Aarav Demo"):
    return next(r for r in rows if r["full_name"] == name)


def test_q01(db):
    rows = query(db, 1)
    assert len(rows) == 4
    assert rows[0]["full_name"] == "Aarav Demo"
    assert rows[0]["playing_role"] == "All-rounder"


def test_q02(db):
    rows = query(db, 2)
    assert len(rows) == 6
    assert rows[0]["match_date"] == "2026-10-23"
    assert rows[-1]["match_date"] == "2026-10-18"


def test_q03(db):
    rows = query(db, 3)
    assert rows[0]["full_name"] == "Diya Demo"  # Tie broken by player id.
    assert rows[0]["career_runs"] == 2220
    assert rows[0]["batting_average"] is None  # Never dismissed.
    aarav = named(rows)
    assert aarav["career_runs"] == 1980
    assert aarav["batting_average"] == 99
    assert aarav["centuries"] == 10


def test_q04(db):
    assert query(db, 4) == [
        {"name": "Demo Oval", "city": "Demo Delhi", "country": "India", "capacity": 60000}
    ]


def test_q05(db):
    assert [(r["name"], r["wins"]) for r in query(db, 5)] == [
        ("India Demo XI", 40),
        ("Australia Demo XI", 20),
    ]


def test_q06(db):
    assert {r["role"]: r["players"] for r in query(db, 6)} == {
        "All-rounder": 2,
        "Batsman": 2,
        "Bowler": 2,
        "Wicket-keeper": 2,
    }


def test_q07(db):
    assert {r["format"]: r["highest_score"] for r in query(db, 7)} == {
        "Test": 166,
        "ODI": 168,
        "T20I": 170,
    }


def test_q08(db):
    rows = query(db, 8)
    assert len(rows) == 1 and rows[0]["start_date"] == "2024-01-01"
    assert rows[0]["planned_matches"] == 60


def test_q09(db):
    rows = query(db, 9)
    assert len(rows) == 6
    r = next(r for r in rows if r["full_name"] == "Aarav Demo" and r["format"] == "ODI")
    assert r["runs"] == 1980 and r["wickets"] == 60


def test_q10(db):
    rows = query(db, 10)
    assert len(rows) == 20
    assert rows[0]["description"] == "Synthetic fixture 60"
    assert rows[0]["winner"] == "India Demo XI"
    assert rows[0]["margin"] == 20 and rows[0]["victory_type"] == "runs"


def test_q11(db):
    r = named(query(db, 11))
    assert (r["test_runs"], r["odi_runs"], r["t20i_runs"], r["overall_batting_average"]) == (
        1940,
        1980,
        2020,
        99,
    )


def test_q12(db):
    rows = query(db, 12)
    assert {(r["name"], r["conditions"]): (r["matches"], r["wins"]) for r in rows} == {
        ("India Demo XI", "Home"): (20, 0),
        ("India Demo XI", "Away"): (40, 40),
        ("Australia Demo XI", "Home"): (20, 0),
        ("Australia Demo XI", "Away"): (40, 20),
    }


def test_q13(db):
    rows = query(db, 13)
    assert rows[0]["combined_runs"] == 336
    assert rows[0]["batter1"] == "Chirag Demo" and rows[0]["batter2"] == "Diya Demo"
    assert all(r["combined_runs"] >= 100 for r in rows)
    assert "proxy" in rows[0]["measure"]


def test_q14(db):
    rows = query(db, 14)
    assert len(rows) == 12
    r = next(r for r in rows if r["full_name"] == "Aarav Demo" and r["venue"] == "Demo Oval")
    expected = statistics.mean((24 + n % 7) / 4 for n in range(0, 60, 3))
    assert r["average_economy"] == pytest.approx(expected)
    assert r["matches"] == 20 and r["wickets"] == 60


def test_q15(db):
    r = named(query(db, 15))
    assert (r["average_runs"], r["close_matches"], r["team_wins"]) == (99, 60, 40)


def test_q16(db):
    rows = query(db, 16)
    r = next(r for r in rows if r["full_name"] == "Aarav Demo" and r["year"] == "2024")
    assert r["matches"] == 24 and r["average_runs_per_match"] == 63
    assert r["average_strike_rate"] == pytest.approx(210)


def test_q17(db):
    rows = query(db, 17)
    assert {
        r["toss_decision"]: (r["matches"], r["toss_winner_wins"], r["win_percentage"]) for r in rows
    } == {"bat": (40, 20, 50), "bowl": (20, 10, 50)}


def test_q18(db):
    r = named(query(db, 18))
    assert (r["matches"], r["wickets"], r["overs_per_match"]) == (40, 120, 4)
    conceded = sum(24 + n % 7 for n in range(60) if n % 3 != 0)
    assert r["economy"] == pytest.approx(conceded / 160)


def test_q19(db):
    r = named(query(db, 19))
    assert r["average_runs"] == 99
    assert r["standard_deviation"] == pytest.approx(math.sqrt(3599 / 3))
    assert r["innings"] == 60


def test_q20(db):
    r = named(query(db, 20))
    assert (r["test_matches"], r["odi_matches"], r["t20_matches"], r["total_matches"]) == (
        20,
        20,
        20,
        60,
    )
    assert (r["test_average"], r["odi_average"], r["t20_average"]) == (97, 99, 101)


def test_q21(db):
    rows = query(db, 21)
    r = next(r for r in rows if r["full_name"] == "Aarav Demo" and r["format"] == "ODI")
    conceded = sum(24 + n % 7 for n in range(1, 60, 3))
    batting = 1980 * 0.01 + 99 * 0.5 + 330 * 0.3
    bowling = 60 * 2 + (50 - conceded / 60) * 0.5 + (6 - conceded / 80) * 2
    assert r["total_score"] == pytest.approx(batting + bowling + 60)
    assert r["batting_points"] == pytest.approx(batting)
    for fmt in ("Test", "ODI", "T20I"):
        fmt_rows = [r for r in rows if r["format"] == fmt]
        assert fmt_rows[0]["rank"] == 1
        assert fmt_rows[0]["total_score"] == max(r["total_score"] for r in fmt_rows)
    nonbowler = next(r for r in rows if r["full_name"] == "Bhavna Demo")
    assert nonbowler["bowling_points"] == 0


def test_q22(db):
    rows = query(db, 22)
    assert sum(r["matches"] for r in rows if r["team"] == "India Demo XI") == 60
    for r in rows:
        assert r["pair_meetings"] == 60
        if r["team"] == "India Demo XI":
            assert r["overall_wins"] == 40
            assert r["overall_win_percentage"] == pytest.approx(200 / 3)
        if r["average_winning_margin_runs"] is not None:
            assert r["average_winning_margin_runs"] == 20
        if r["average_winning_margin_wickets"] is not None:
            assert r["average_winning_margin_wickets"] == 4


def test_q23(db):
    r = named(query(db, 23))
    assert r["last5_average"] == 154 and r["last10_average"] == 149
    assert r["performances"] == 10 and r["scores_above50"] == 10
    assert r["standard_deviation"] == pytest.approx(statistics.pstdev(range(140, 160, 2)))
    assert r["form_classification"] == "Excellent Form"


def test_q24(db):
    rows = query(db, 24)
    assert len(rows) == 6
    assert rows[0]["average_combined_runs"] == 218
    assert rows[0]["highest_score"] == 336
    assert rows[0]["partnerships"] == 60 and rows[0]["exceeding50"] == 60
    assert rows[0]["success_percentage"] == 100 and rows[0]["rank"] == 1


def test_q25(db):
    rows = [r for r in query(db, 25) if r["full_name"] == "Aarav Demo"]
    assert len(rows) == 10
    assert rows[0]["average_runs"] == 45 and rows[0]["quarter_trend"] == "Baseline"
    assert rows[1]["average_runs"] == 57 and rows[1]["runs_change"] == 12
    assert all(r["career_trajectory"] == "Career Ascending" for r in rows)
    assert rows[-1]["quarter"] == 4 and rows[-1]["year"] == 2026


def test_all_queries_on_empty_database(tmp_path):
    from database.connection import initialize

    path = tmp_path / "empty.sqlite3"
    initialize(path)
    for n in range(1, 26):
        assert execute(path, n, DEMO_DATE) == []


def test_test_match_multiple_innings_do_not_double_count(db):
    with connect(db) as c:
        c.execute("INSERT INTO innings VALUES(9999,1,3,1,100,1,60)")
        c.execute("INSERT INTO batting VALUES(9999,1,1,100,60,1)")
    assert named(query(db, 15))["close_matches"] == 60
    assert named(query(db, 20))["test_matches"] == 20
    assert named(query(db, 11))["overall_batting_average"] == pytest.approx(6040 / 61)


def test_thresholds_strict_and_minimum_balls(db):
    with connect(db) as c:
        c.execute("UPDATE batting SET balls=9 WHERE player_id=1")
        c.execute("UPDATE bowling SET balls=23 WHERE player_id=1")
    assert all(r["full_name"] != "Aarav Demo" for r in query(db, 19))
    assert all(r["full_name"] != "Aarav Demo" for r in query(db, 14))


@pytest.mark.parametrize(
    "runs,label", [(40, "Good Form"), (25, "Average Form"), (10, "Poor Form"), (50, "Good Form")]
)
def test_recent_form_classification_boundaries(db, runs, label):
    with connect(db) as c:
        c.execute("UPDATE batting SET runs=? WHERE player_id=1", (runs,))
    r = named(query(db, 23))
    assert r["form_classification"] == label
    assert r["standard_deviation"] == 0
    if runs == 50:
        assert r["scores_above50"] == 0  # Strict source-document threshold.


@pytest.mark.parametrize("declining,label", [(True, "Career Declining"), (False, "Career Stable")])
def test_career_phase_alternatives(db, declining, label):
    with connect(db) as c:
        # Match ids are 1..60; formulas are independent deterministic oracles.
        c.execute(
            "UPDATE batting SET runs=(SELECT CASE WHEN ? THEN 200-2*(i.match_id-1) ELSE 50 END FROM innings i WHERE i.id=batting.innings_id) WHERE player_id=1",
            (declining,),
        )
    rows = [r for r in query(db, 25) if r["full_name"] == "Aarav Demo"]
    assert len(rows) == 10
    assert all(r["career_trajectory"] == label for r in rows)
    assert rows[1]["quarter_trend"] == ("Declining" if declining else "Stable")


def test_minimum_partnership_and_quarter_eligibility(db):
    with connect(db) as c:
        c.execute(
            "DELETE FROM batting WHERE player_id=1 AND innings_id IN (SELECT id FROM innings WHERE match_id>4)"
        )
    assert all(r["batter1"] != "Aarav Demo" and r["batter2"] != "Aarav Demo" for r in query(db, 24))
    # DNB does not erase participation; remove appearances to test the quarter minimum.
    assert any(r["full_name"] == "Aarav Demo" for r in query(db, 25))
    with connect(db) as c:
        c.execute("DELETE FROM participants WHERE player_id=1 AND match_id>4")
    assert all(r["full_name"] != "Aarav Demo" for r in query(db, 25))


def test_recent_date_window_excludes_future_and_boundary(db):
    with connect(db) as c:
        c.execute("UPDATE matches SET match_date='2026-10-25' WHERE id=60")
        c.execute("UPDATE matches SET match_date='2026-09-24' WHERE id=59")
        c.execute("UPDATE matches SET match_date='2026-09-23' WHERE id=58")
    rows = query(db, 2)
    assert len(rows) == 4
    assert rows[-1]["match_date"] == "2026-09-24"


def test_canonical_head_to_head_and_threshold(db):
    with connect(db) as c:
        c.execute("UPDATE matches SET team1_id=2,team2_id=1 WHERE id%2=0")
    assert all(r["pair_meetings"] == 60 for r in query(db, 22))
    with connect(db) as c:
        c.execute("UPDATE matches SET match_date='2000-01-01' WHERE id>4")
    assert query(db, 22) == []


def test_fielding_only_player_has_no_invented_batting_or_bowling_bonus(db):
    with connect(db) as c:
        c.execute(
            "INSERT INTO players(id,full_name,country,role,batting_style,bowling_style) VALUES(9,'Fielding Only','India','Wicket-keeper','Unknown','None')"
        )
        c.execute("INSERT INTO participants VALUES(1,9,1)")
        c.execute("INSERT INTO fielding VALUES(1,9,2,1)")
    r = named(query(db, 21), "Fielding Only")
    assert r["batting_points"] == 0
    assert r["bowling_points"] == 0
    assert r["fielding_points"] == 11 and r["total_score"] == 11


def test_yearly_runs_include_did_not_bat_appearances(db):
    with connect(db) as c:
        c.execute(
            "DELETE FROM batting WHERE player_id=1 AND innings_id IN (SELECT id FROM innings WHERE match_id BETWEEN 5 AND 24)"
        )
    row = next(r for r in query(db, 16) if r["full_name"] == "Aarav Demo" and r["year"] == "2024")
    assert row["matches"] == 24
    assert row["average_runs_per_match"] == pytest.approx((40 + 42 + 44 + 46) / 24)


def test_recent_form_uses_matches_not_test_innings(db):
    with connect(db) as c:
        c.execute("INSERT INTO innings VALUES(9999,58,3,1,100,1,60)")
        c.execute("INSERT INTO batting VALUES(9999,1,1,100,60,1)")
    row = named(query(db, 23))
    assert row["performances"] == 10
    assert row["last5_average"] == 174  # Five match totals; one Test has an extra 100.
    assert row["last10_average"] == 159


def test_quarter_changes_do_not_bridge_missing_quarters(db):
    rows = [r for r in query(db, 25) if r["full_name"] == "Aarav Demo"]
    assert rows[-1]["year"] == 2026 and rows[-1]["quarter"] == 4
    assert rows[-1]["runs_change"] is None
    assert rows[-1]["strike_rate_change"] is None
    assert rows[-1]["quarter_trend"] == "Gap: no prior qualifying quarter"


def test_yearly_eligible_status_is_shared_by_counts_and_runs(db):
    with connect(db) as c:
        c.execute("UPDATE matches SET status='Upcoming' WHERE id=1")
        c.execute("UPDATE matches SET status='Abandoned' WHERE id=2")
    row = next(r for r in query(db, 16) if r["full_name"] == "Aarav Demo" and r["year"] == "2024")
    assert row["matches"] == 23
    assert row["average_runs_per_match"] == pytest.approx((1512 - 40) / 23)


def test_quarter_analysis_uses_explicit_recent_window(db):
    with connect(db) as c:
        c.execute("UPDATE matches SET match_date='2000-01-01' WHERE id<=48")
    assert query(db, 25) == []  # Only two recent qualifying quarters remain.
