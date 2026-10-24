"""Retain fetched career tables as provider snapshots, separate from match totals."""

import json
from datetime import datetime, timezone
from api import players
from api.client import ApiError
from database.connection import connect
from services.ingestion import snapshot


def fetch_player(path, client, provider_id):
    profile = players.profile(client, provider_id)
    batting = players.batting(client, provider_id)
    bowling = players.bowling(client, provider_id)
    if not profile.get("name"):
        raise ApiError("Player profile missing name.", "schema")
    tables = []
    for discipline, payload in [("batting", batting), ("bowling", bowling)]:
        if not isinstance(payload.get("headers"), list) or not isinstance(
            payload.get("values"), list
        ):
            raise ApiError("Player statistics missing headers/values table.", "schema")
        headers = payload["headers"]
        columns = {str(h).upper(): i for i, h in enumerate(headers)}
        for fmt in ("Test", "ODI", "T20I", "T20"):
            idx = columns.get(fmt.upper())
            if idx is not None:
                stats = {
                    row.get("values", [""])[0]: row["values"][idx]
                    for row in payload["values"]
                    if isinstance(row, dict) and len(row.get("values", [])) > idx
                }
                tables.append((fmt, discipline, stats))
    with connect(path) as c:
        if c.execute("SELECT 1 FROM metadata WHERE key='seed_version'").fetchone():
            raise ValueError("Provider ingestion requires a separate live database.")
        role = profile.get("role", "")
        role = role if role in ("Batsman", "Bowler", "All-rounder", "Wicket-keeper") else "Unknown"
        c.execute(
            "INSERT INTO players(full_name,country,role,batting_style,bowling_style,source,external_id) VALUES(?,?,?,?,?,?,?) ON CONFLICT(external_id) DO UPDATE SET full_name=excluded.full_name,country=excluded.country,role=excluded.role,batting_style=excluded.batting_style,bowling_style=excluded.bowling_style",
            (
                profile["name"],
                profile.get("intlTeam", "Unknown"),
                role,
                profile.get("bat", "Unknown"),
                profile.get("bowl", "Unknown"),
                "rapidapi-cricbuzz-v1",
                provider_id,
            ),
        )
        pid = c.execute("SELECT id FROM players WHERE external_id=?", (provider_id,)).fetchone()[0]
        for fmt, discipline, stats in tables:
            c.execute(
                "INSERT INTO player_career_stats VALUES(?,?,?,?,?,?) ON CONFLICT(player_id,format,discipline) DO UPDATE SET payload=excluded.payload,fetched_at=excluded.fetched_at",
                (
                    pid,
                    fmt,
                    discipline,
                    json.dumps(stats),
                    datetime.now(timezone.utc).isoformat(),
                    "rapidapi-cricbuzz-v1",
                ),
            )
        for name, payload in [("profile", profile), ("batting", batting), ("bowling", bowling)]:
            snapshot(c, f"player/{provider_id}/{name}", payload)
    return profile, batting, bowling
