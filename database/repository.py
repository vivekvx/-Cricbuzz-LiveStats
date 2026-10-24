"""Parameterized, persistent CRUD. Referential restrictions are intentional."""

from analytics.validations import player_fields
from database.connection import connect, read_query


def players(path, search=""):
    return read_query(
        path,
        "SELECT * FROM players WHERE full_name LIKE :term ORDER BY full_name",
        {"term": f"%{search}%"},
    )


def create_player(path, name, country, role, batting_style, bowling_style):
    values = player_fields(name, country, role, batting_style, bowling_style)
    with connect(path) as c:
        return c.execute(
            "INSERT INTO players(full_name,country,role,batting_style,bowling_style) VALUES(?,?,?,?,?)",
            values,
        ).lastrowid


def update_player(path, player_id, name, country, role, batting_style, bowling_style):
    values = player_fields(name, country, role, batting_style, bowling_style)
    with connect(path) as c:
        if (
            c.execute(
                "UPDATE players SET full_name=?,country=?,role=?,batting_style=?,bowling_style=? WHERE id=?",
                values + [player_id],
            ).rowcount
            != 1
        ):
            raise ValueError("Player no longer exists.")


def delete_player(path, player_id):
    with connect(path) as c:
        if c.execute("DELETE FROM players WHERE id=?", (player_id,)).rowcount != 1:
            raise ValueError("Player no longer exists.")


def save_batting(path, innings_id, player_id, position, runs, balls, dismissed):
    """Create/update a batting row with a matching team participant."""
    if not all(
        isinstance(x, int) for x in (innings_id, player_id, position, runs, balls, dismissed)
    ):
        raise ValueError("Statistics must be integers.")
    if not 1 <= position <= 11 or runs < 0 or balls < 0 or dismissed not in (0, 1):
        raise ValueError("Invalid batting statistics.")
    with connect(path) as c:
        valid = c.execute(
            "SELECT 1 FROM innings i JOIN participants p ON p.match_id=i.match_id AND p.team_id=i.team_id WHERE i.id=? AND p.player_id=?",
            (innings_id, player_id),
        ).fetchone()
        if not valid:
            raise ValueError("Player must be a participant for the batting team in this match.")
        c.execute(
            "INSERT INTO batting VALUES(?,?,?,?,?,?) ON CONFLICT(innings_id,player_id) DO UPDATE SET position=excluded.position,runs=excluded.runs,balls=excluded.balls,dismissed=excluded.dismissed",
            (innings_id, player_id, position, runs, balls, dismissed),
        )


def delete_batting(path, innings_id, player_id):
    with connect(path) as c:
        if (
            c.execute(
                "DELETE FROM batting WHERE innings_id=? AND player_id=?", (innings_id, player_id)
            ).rowcount
            != 1
        ):
            raise ValueError("Batting record not found.")


def save_bowling(path, innings_id, player_id, balls, runs, wickets):
    if min(balls, runs, wickets) < 0 or wickets > 10:
        raise ValueError("Invalid bowling statistics.")
    with connect(path) as c:
        valid = c.execute(
            "SELECT 1 FROM innings i JOIN participants p ON p.match_id=i.match_id AND p.team_id<>i.team_id WHERE i.id=? AND p.player_id=?",
            (innings_id, player_id),
        ).fetchone()
        if not valid:
            raise ValueError("Bowler must be an opposing team participant.")
        c.execute(
            "INSERT INTO bowling VALUES(?,?,?,?,?) ON CONFLICT(innings_id,player_id) DO UPDATE SET balls=excluded.balls,runs=excluded.runs,wickets=excluded.wickets",
            (innings_id, player_id, balls, runs, wickets),
        )


def delete_bowling(path, innings_id, player_id):
    with connect(path) as c:
        if (
            c.execute(
                "DELETE FROM bowling WHERE innings_id=? AND player_id=?", (innings_id, player_id)
            ).rowcount
            != 1
        ):
            raise ValueError("Bowling record not found.")
