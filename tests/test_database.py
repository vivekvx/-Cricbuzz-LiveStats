import sqlite3
import pytest
from database.connection import connect, initialize, read_query
from database.seed import seed


def test_seed_and_initialization_idempotent(db):
    initialize(db)
    seed(db)
    assert read_query(db, "SELECT COUNT(*) n FROM matches")[0]["n"] == 60
    assert read_query(db, "SELECT COUNT(*) n FROM batting")[0]["n"] == 480
    with connect(db) as c:
        assert c.execute("PRAGMA foreign_key_check").fetchall() == []
        assert c.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_foreign_keys_and_constraints(db):
    with pytest.raises(sqlite3.IntegrityError), connect(db) as c:
        c.execute("INSERT INTO batting VALUES(999999,1,1,1,1,1)")
    with pytest.raises(sqlite3.IntegrityError), connect(db) as c:
        c.execute("UPDATE batting SET runs=-1 WHERE player_id=1")
    assert read_query(db, "SELECT MIN(runs) n FROM batting")[0]["n"] == 40


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM players",
        'UPDATE players SET country="X"',
        "DROP TABLE players",
        "PRAGMA foreign_keys=OFF",
        "PRAGMA table_info(players)",
        'ATTACH DATABASE ":memory:" AS x',
        "CREATE TEMP TABLE x(a)",
        'SELECT load_extension("x")',
        "SELECT 1; DELETE FROM players;",
        "WITH x AS (SELECT 1) DELETE FROM players",
        "VACUUM",
        "BEGIN",
    ],
)
def test_read_only_rejects_mutations(db, sql):
    with pytest.raises((sqlite3.Error, ValueError)):
        read_query(db, sql)
    assert len(read_query(db, "SELECT * FROM players")) == 8


def test_read_only_cte_and_limits(db):
    assert read_query(db, "WITH x AS (SELECT 7 n) SELECT n FROM x") == [{"n": 7}]
    with pytest.raises(ValueError, match="exceeds"):
        read_query(db, "SELECT * FROM players", limit=1)
    with pytest.raises(sqlite3.Error, match="interrupted"):
        read_query(
            db, "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n) SELECT sum(x) FROM n"
        )


def test_sql_only_seed_reproducible(tmp_path):
    from pathlib import Path

    path = tmp_path / "sql_seed.sqlite3"
    initialize(path)
    source = Path(__file__).resolve().parents[1] / "data/sample_data/seed.sql"
    with connect(path) as c:
        c.executescript(source.read_text())
        c.executescript(source.read_text())
        assert c.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == 60
        assert c.execute("SELECT COUNT(*) FROM batting").fetchone()[0] == 480
        assert c.execute("PRAGMA foreign_key_check").fetchall() == []
