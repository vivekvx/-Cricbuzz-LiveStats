"""All JSON fixtures are explicitly synthetic contract examples, not captured responses."""

import json
from pathlib import Path
from unittest.mock import Mock
import requests
import pytest
from api.client import ApiError, Client, identifier
from api import matches, players
from config import database_path
from database.connection import initialize, read_query
from services.ingestion import ingest_matches, ingest_scorecard
from services.normalization import normalize_matches, normalize_scorecard, cricket_format
from services.player_service import fetch_player

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def payload():
    return json.loads((FIXTURES / "matches.json").read_text())


@pytest.fixture
def card():
    return json.loads((FIXTURES / "scorecard.json").read_text())


def response(status=200, payload=None):
    return Mock(
        status_code=status,
        headers={"Retry-After": "60"},
        json=Mock(return_value=payload if payload is not None else {}),
    )


def client(responses):
    session = Mock()
    session.get.side_effect = responses
    return Client(key="unit-test-key", session=session, sleep=Mock())


def test_missing_credentials():
    c = Client(key="", session=Mock())
    with pytest.raises(ApiError, match="missing"):
        c.get("/matches/v1/live")
    c.session.get.assert_not_called()


@pytest.mark.parametrize(
    "status,kind",
    [
        (401, "credentials"),
        (403, "credentials"),
        (404, "not_found"),
        (429, "rate_limit"),
        (400, "provider"),
    ],
)
def test_failures(status, kind):
    c = client([response(status)])
    with pytest.raises(ApiError) as e:
        c.get("/matches/v1/live")
    assert e.value.kind == kind
    assert c.session.get.call_count == 1
    assert "unit-test-key" not in str(e.value)


def test_bounded_retry_and_timeout():
    c = client([requests.Timeout(), response(503), response(200, {"typeMatches": []})])
    assert c.get("/matches/v1/live") == {"typeMatches": []}
    assert c.session.get.call_count == 3
    assert c.session.get.call_args.kwargs["timeout"] == (5, 20)
    assert c.sleep.call_count == 2
    with pytest.raises(ApiError):
        client([response(500)] * 3).get("/matches/v1/live")
    with pytest.raises(ApiError):
        client([requests.ConnectionError()] * 3).get("/matches/v1/live")


def test_schema_and_input_failures():
    with pytest.raises(ApiError):
        client([response(200, [])]).get("/matches/v1/live")
    bad = response()
    bad.json.side_effect = ValueError()
    with pytest.raises(ApiError):
        client([bad]).get("/matches/v1/live")
    for invalid in ("../bad", 0, True, "1?secret"):
        with pytest.raises(ValueError):
            identifier(invalid)
    with pytest.raises(ValueError):
        Client(base_url="http://example.com")
    with pytest.raises(ValueError):
        Client(key="x").get("//evil.example")


def test_normalization(payload, card):
    m = normalize_matches(payload)[0]
    assert m["id"] == 9001 and m["format"] == "ODI"
    assert m["status"] == "Live"
    innings = normalize_scorecard(card)[0]
    assert innings["balls"] == 122 and innings["bowlers"][0]["balls"] == 26
    assert innings["batters"][0]["dismissed"] == 0
    assert cricket_format("T20") == "T20"
    assert cricket_format("T20I") == "T20I"
    assert cricket_format("UNKNOWN") == "Other"
    assert normalize_matches({"typeMatches": []}) == []
    with pytest.raises(ApiError):
        normalize_matches({})
    with pytest.raises(ApiError):
        normalize_scorecard({"scoreCard": [{"inningsId": 1}]})


def test_ingestion_idempotence_and_mode_separation(tmp_path, db, payload, card):
    path = tmp_path / "live.sqlite3"
    initialize(path)
    ingest_matches(path, payload)
    ingest_matches(path, payload)
    ingest_scorecard(path, 9001, card)
    ingest_scorecard(path, 9001, card)
    assert len(read_query(path, "SELECT * FROM matches")) == 1
    assert len(read_query(path, "SELECT * FROM innings")) == 1
    assert len(read_query(path, "SELECT * FROM batting")) == 1
    assert read_query(path, "SELECT balls FROM bowling") == [{"balls": 26}]
    assert (
        read_query(path, "SELECT source FROM api_snapshots")[0]["source"] == "rapidapi-cricbuzz-v1"
    )
    assert read_query(path, "SELECT winner_id FROM matches")[0]["winner_id"] is None
    assert read_query(path, "SELECT role FROM players")[0]["role"] == "Unknown"
    with pytest.raises(ValueError, match="separate"):
        ingest_matches(db, payload)
    assert len(read_query(db, "SELECT * FROM matches")) == 60
    assert database_path("Live API") != database_path("Sample Data")


def test_endpoint_adapters():
    c = Mock()
    matches.match_list(c)
    c.get.assert_called_with("/matches/v1/live")
    matches.scorecard(c, 123)
    c.get.assert_called_with("/mcenter/v1/123/scard")
    players.batting(c, 10)
    c.get.assert_called_with("/stats/v1/player/10/batting")
    players.bowling(c, 10)
    c.get.assert_called_with("/stats/v1/player/10/bowling")
    matches.series_matches(c, 7)
    c.get.assert_called_with("/series/v1/7")
    matches.venue_details(c, 5)
    c.get.assert_called_with("/venues/v1/5")


def test_player_snapshot(tmp_path):
    path = tmp_path / "live.sqlite3"
    initialize(path)
    c = Mock()
    c.get.side_effect = [
        {"name": "Fixture Batter", "role": "Batsman", "intlTeam": "India"},
        {"headers": ["ROWHEADER", "Test", "ODI"], "values": [{"values": ["Runs", "100", "200"]}]},
        {"headers": ["ROWHEADER", "ODI"], "values": [{"values": ["Wkts", "10"]}]},
    ]
    fetch_player(path, c, 8001)
    rows = read_query(path, "SELECT * FROM player_career_stats ORDER BY discipline,format")
    assert len(rows) == 3
    assert json.loads(rows[0]["payload"]) == {"Runs": "200"}
    assert (
        read_query(path, "SELECT * FROM career") == []
    )  # Never mix snapshot totals into match aggregates.


def test_international_vs_domestic_t20(payload):
    group = payload["typeMatches"][0]
    group["seriesMatches"][1]["seriesAdWrapper"]["matches"][0]["matchInfo"]["matchFormat"] = "T20"
    group["matchType"] = "International"
    assert normalize_matches(payload)[0]["format"] == "T20I"
    group["matchType"] = "League"
    assert normalize_matches(payload)[0]["format"] == "T20"


def test_captured_current_scorecard(tmp_path, payload):
    current = json.loads((FIXTURES / "current_scorecard.json").read_text())
    from services.normalization import normalize_current_scorecard

    teams = {"New Zealand": 13, "India": 2}
    cards = normalize_current_scorecard(current, teams)
    assert [c["runs"] for c in cards] == [180, 127]
    assert [c["balls"] for c in cards] == [120, 97]
    assert [sum(p["dismissed"] for p in c["batters"]) for c in cards] == [5, 6]
    assert cards[0]["bat_team"] == 13 and cards[0]["bowl_team"] == 2
    assert sum(not p["did_not_bat"] for c in cards for p in c["batters"]) == 15
    assert sum(len(c["bowlers"]) for c in cards) == 12
    with pytest.raises(ApiError, match="team names"):
        normalize_current_scorecard(current, {"Unrelated": 1, "India": 2})
    path = tmp_path / "live.sqlite3"
    initialize(path)
    match = payload["typeMatches"][0]["seriesMatches"][1]["seriesAdWrapper"]["matches"][0][
        "matchInfo"
    ]
    match["matchId"] = 161201
    match["team1"] = {"teamId": 13, "teamName": "New Zealand"}
    match["team2"] = {"teamId": 2, "teamName": "India"}
    ingest_matches(path, payload)
    ingest_scorecard(path, 161201, current)
    ingest_scorecard(path, 161201, current)
    assert len(read_query(path, "SELECT * FROM batting")) == 15
    assert len(read_query(path, "SELECT * FROM bowling")) == 12


def test_profile_null_bowling_style_and_keeper_role(tmp_path):
    path = tmp_path / "live.sqlite3"
    initialize(path)
    c = Mock()
    c.get.side_effect = [
        {
            "name": "Fixture Keeper",
            "fullName": "Fixture Full Keeper",
            "role": "WK-Batsman",
            "intlTeam": "India",
            "bat": "Right Handed Bat",
            "bowl": None,
        },
        {"headers": ["ROWHEADER", "ODI"], "values": [{"values": ["Runs", "100"]}]},
        {"headers": ["ROWHEADER", "ODI"], "values": [{"values": ["Wickets", "0"]}]},
    ]
    fetch_player(path, c, 12345)
    player = read_query(path, "SELECT * FROM players")[0]
    assert player["role"] == "Wicket-keeper"
    assert player["bowling_style"] == "Unknown"
    assert player["full_name"] == "Fixture Full Keeper"


def test_domestic_and_unofficial_games_are_not_international_formats(payload):
    group = payload["typeMatches"][0]
    match = group["seriesMatches"][1]["seriesAdWrapper"]["matches"][0]["matchInfo"]
    group["matchType"] = "Domestic"
    for fmt in ["TEST", "ODI"]:
        match["matchFormat"] = fmt
        assert normalize_matches(payload)[0]["format"] == "Other"
    group["matchType"] = "International"
    match["matchFormat"] = "TEST"
    match["matchDesc"] = "1st Unofficial Test"
    assert normalize_matches(payload)[0]["format"] == "Other"
    match["matchDesc"] = "2nd Test"
    assert normalize_matches(payload)[0]["format"] == "Test"
    match["matchDesc"] = "2-Day Warm-Up Match"
    assert normalize_matches(payload)[0]["format"] == "Other"


def test_completed_result_and_schedule_updates_are_persisted(tmp_path, payload):
    path = tmp_path / "live.sqlite3"
    initialize(path)
    info = payload["typeMatches"][0]["seriesMatches"][1]["seriesAdWrapper"]["matches"][0][
        "matchInfo"
    ]
    info["state"] = "Complete"
    info["status"] = "Fixture Team A won by 4 wkts"
    ingest_matches(path, payload)
    assert read_query(path, "SELECT winner_id,margin,victory_type FROM matches") == [
        {"winner_id": 901, "margin": 4, "victory_type": "wickets"}
    ]
    info["startDate"] = "1792320000000"
    ingest_matches(path, payload)
    assert read_query(path, "SELECT match_date FROM matches")[0]["match_date"] == "2026-10-18"


def test_explicit_result_parser_never_guesses():
    from services.results import result_fields

    teams = [{"teamName": "India", "teamId": 2}, {"teamName": "South Africa", "teamId": 11}]
    assert result_fields("India won by 4 wkts", teams) == (2, 4, "wickets")
    assert result_fields("South Africa won by an innings and 31 runs", teams) == (11, 31, "innings")
    assert result_fields("India won by 20 runs (DLS Method)", teams) == (2, 20, "runs")
    assert result_fields("India need 4 runs", teams) == (None, None, None)
    assert result_fields("Match drawn", teams) == (None, None, None)
    assert result_fields("Unknown Team won by 2 runs", teams) == (None, None, None)


def test_legacy_scorecard_excludes_did_not_bat(tmp_path, payload, card):
    path = tmp_path / "legacy.sqlite3"
    initialize(path)
    ingest_matches(path, payload)
    card["scoreCard"][0]["batTeamDetails"]["batsmenData"]["bat_2"] = {
        "batId": 8003,
        "batName": "Bench Fixture",
        "runs": 0,
        "balls": 0,
        "outDesc": "",
    }
    ingest_scorecard(path, 9001, card)
    assert len(read_query(path, "SELECT * FROM batting")) == 1
    assert len(read_query(path, "SELECT * FROM participants")) == 3


def test_incomplete_refresh_never_erases_a_confirmed_result(tmp_path, payload):
    path = tmp_path / "live.sqlite3"
    initialize(path)
    info = payload["typeMatches"][0]["seriesMatches"][1]["seriesAdWrapper"]["matches"][0][
        "matchInfo"
    ]
    info["state"] = "Complete"
    info["status"] = "Fixture Team A won by 20 runs"
    ingest_matches(path, payload)
    ingest_scorecard(path, 9001, {"scorecard": [], "ismatchcomplete": True})
    assert read_query(path, "SELECT winner_id,margin FROM matches") == [
        {"winner_id": 901, "margin": 20}
    ]
    info["status"] = ""
    ingest_matches(path, payload)
    assert read_query(path, "SELECT winner_id,margin FROM matches") == [
        {"winner_id": 901, "margin": 20}
    ]
    info["state"] = "In Progress"
    info["status"] = "Fixture Team B need 10 runs"
    ingest_matches(path, payload)
    assert read_query(path, "SELECT status,winner_id,margin FROM matches") == [
        {"status": "Complete", "winner_id": 901, "margin": 20}
    ]
    info["state"] = "Complete"
    info["status"] = "Match drawn"
    ingest_matches(path, payload)
    assert read_query(path, "SELECT winner_id,margin FROM matches") == [
        {"winner_id": None, "margin": None}
    ]


def test_international_t20_warmup_is_not_t20i():
    assert cricket_format("T20", True, "1st Warm-up match") == "Other"
    assert cricket_format("T20", True, "Unofficial T20") == "Other"
    assert cricket_format("T20", True, "2nd T20I") == "T20I"
