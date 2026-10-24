"""Regression checks discovered by auditing real provider payloads."""

import json
from pathlib import Path
import pytest
from datetime import datetime, timezone
from database.connection import initialize, connect, read_query
from analytics.coverage import live_warnings
from services.freshness import provider_timestamp


def test_provider_time_parsing():
    expected = datetime.fromtimestamp(1792853474, timezone.utc)
    assert provider_timestamp({"responseLastUpdated": 1792853474}) == expected
    assert provider_timestamp({"responselastupdated": 1792853474000}) == expected
    assert provider_timestamp({}) is None
    assert provider_timestamp({"responselastupdated": "invalid"}) is None


def test_missing_live_metadata_is_disclosed(tmp_path):
    path = tmp_path / "live.sqlite3"
    initialize(path)
    assert any("partial ranking" in w for w in live_warnings(path, 21))
    assert any("Toss data" in w for w in live_warnings(path, 17))
    assert any("capacities" in w for w in live_warnings(path, 4))
    assert any("Series metadata" in w for w in live_warnings(path, 8))


def test_old_saved_domestic_formats_are_repaired(tmp_path):
    from pathlib import Path
    from services.ingestion import ingest_matches

    path = tmp_path / "old.sqlite3"
    initialize(path)
    payload = json.loads((Path(__file__).parent / "fixtures/matches.json").read_text())
    payload["typeMatches"][0]["matchType"] = "Domestic"
    ingest_matches(path, payload)
    with connect(path) as c:
        c.execute("UPDATE matches SET format='ODI'")
        c.execute("DELETE FROM metadata WHERE key='live_normalization_v3'")
    initialize(path)
    assert read_query(path, "SELECT format FROM matches") == [{"format": "Other"}]
    initialize(path)
    assert len(read_query(path, "SELECT * FROM matches")) == 1


CASES = json.loads((Path(__file__).parent / "fixtures/audited_scorecards.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=["T20I", "ODI", "Test"])
def test_audited_three_formats_match_independent_scorecard_totals(tmp_path, case):
    from services.ingestion import ingest_matches, ingest_scorecard

    path = tmp_path / "live.sqlite3"
    initialize(path)
    info = case["match"]
    expected = case["expected"]
    payload = {
        "typeMatches": [
            {
                "matchType": "International",
                "seriesMatches": [{"seriesAdWrapper": {"matches": [{"matchInfo": info}]}}],
            }
        ]
    }
    ingest_matches(path, payload)
    cards = ingest_scorecard(path, info["matchId"], case["card"])
    assert [c["runs"] for c in cards] == expected["runs"]
    assert [c["balls"] for c in cards] == expected["balls"]
    assert [sum(b["dismissed"] for b in c["batters"]) for c in cards] == expected["dismissals"]
    for source, card in zip(case["card"]["scorecard"], cards):
        assert sum(b["runs"] for b in source["batsman"]) + source["extras"]["total"] == card["runs"]
        assert sum(b["balls"] for b in source["bowler"]) == card["balls"]
    row = read_query(path, "SELECT * FROM matches")[0]
    assert (row["winner_id"], row["margin"], row["victory_type"]) == (
        expected["winner"],
        expected["margin"],
        expected["method"],
    )
    assert row["batting_first_id"] == cards[0]["bat_team"]
    before = len(read_query(path, "SELECT * FROM batting"))
    ingest_scorecard(path, info["matchId"], case["card"])
    assert len(read_query(path, "SELECT * FROM batting")) == before
