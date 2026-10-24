import sqlite3
import pytest
from database import repository as r
from database.connection import read_query


def test_player_lifecycle_persists(db):
    pid = r.create_player(db, "Test Learner", "India", "Batsman", "Left-hand bat", "None")
    assert r.players(db, "Learner")[0]["id"] == pid
    r.update_player(db, pid, "Updated Learner", "Australia", "Bowler", "Right-hand bat", "Spin")
    assert r.players(db, "Updated Learner")[0]["country"] == "Australia"
    r.delete_player(db, pid)
    assert r.players(db, "Learner") == []


def test_validation_duplicates_and_references(db):
    with pytest.raises(ValueError):
        r.create_player(db, " ", "India", "Batsman", "Left", "None")
    with pytest.raises(sqlite3.IntegrityError):
        r.create_player(db, "aarav demo", "India", "Batsman", "Left", "None")
    with pytest.raises(sqlite3.IntegrityError):
        r.delete_player(db, 1)
    with pytest.raises(ValueError):
        r.update_player(db, 900, "Missing", "India", "Batsman", "Left", "None")
    assert r.players(db, "' OR 1=1 --") == []


def test_match_stats_lifecycle(db):
    # Match 1: India bats first (innings 11); Australia bowls.
    r.save_batting(db, 11, 1, 1, 123, 100, 1)
    assert read_query(db, "SELECT runs FROM batting WHERE innings_id=11 AND player_id=1") == [
        {"runs": 123}
    ]
    r.delete_batting(db, 11, 1)
    r.save_batting(db, 11, 1, 1, 42, 30, 0)
    assert (
        read_query(db, "SELECT dismissed FROM batting WHERE innings_id=11 AND player_id=1")[0][
            "dismissed"
        ]
        == 0
    )
    r.save_bowling(db, 11, 5, 25, 20, 2)
    assert (
        read_query(db, "SELECT balls FROM bowling WHERE innings_id=11 AND player_id=5")[0]["balls"]
        == 25
    )
    r.delete_bowling(db, 11, 5)
    assert read_query(db, "SELECT * FROM bowling WHERE innings_id=11 AND player_id=5") == []
    with pytest.raises(ValueError):
        r.save_batting(db, 11, 5, 1, 10, 10, 1)
    with pytest.raises(ValueError):
        r.save_bowling(db, 11, 1, 24, 10, 1)
