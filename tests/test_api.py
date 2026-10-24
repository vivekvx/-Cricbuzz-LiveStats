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
