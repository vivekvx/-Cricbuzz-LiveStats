"""Atomic provider ingestion with upserts and payload provenance."""

import json
from datetime import datetime, timezone
from database.connection import connect
from services.normalization import normalize_matches, normalize_scorecard
from services.results import result_fields, explicitly_no_winner


def snapshot(c, endpoint, payload):
    c.execute(
        "INSERT INTO api_snapshots VALUES(?,?,?,?) ON CONFLICT(endpoint) DO UPDATE SET payload=excluded.payload,fetched_at=excluded.fetched_at",
        (
            endpoint,
            json.dumps(payload),
            datetime.now(timezone.utc).isoformat(),
            "rapidapi-cricbuzz-v1",
        ),
    )


def ingest_matches(path, payload, category="live"):
    matches = normalize_matches(payload)
    with connect(path) as c:
        if c.execute("SELECT 1 FROM metadata WHERE key='seed_version'").fetchone():
            raise ValueError("Provider ingestion requires a separate, unseeded live database.")
        for m in matches:
            existing = c.execute("SELECT status FROM matches WHERE id=?", (m["id"],)).fetchone()
            if (
                existing
                and existing["status"] == "Complete"
                and m["status"] in ("Live", "Upcoming")
            ):
                # A cached list must not undo a terminal result already supplied by a card.
                continue
            for t in m["teams"]:
                # Team country is not reliably provided by this endpoint. Unknown stays unknown.
                c.execute(
                    "INSERT INTO teams(id,name,country,source) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name",
                    (
                        t["teamId"],
                        t["teamName"],
                        t.get("country", "Unknown"),
                        "rapidapi-cricbuzz-v1",
                    ),
                )
            v = m["venue"]
            vid = v.get("id")
            if vid:
                c.execute(
                    "INSERT INTO venues VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,city=excluded.city,country=excluded.country",
                    (
                        vid,
                        v.get("ground", "Unknown"),
                        v.get("city", "Unknown"),
                        v.get("country", "Unknown"),
                        None,
                        "rapidapi-cricbuzz-v1",
                    ),
                )
            c.execute(
                """INSERT INTO matches(id,description,team1_id,team2_id,venue_id,match_date,format,status,status_text,source,winner_id,margin,victory_type)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET description=excluded.description,team1_id=excluded.team1_id,team2_id=excluded.team2_id,match_date=excluded.match_date,venue_id=excluded.venue_id,format=excluded.format,status=excluded.status,status_text=CASE WHEN excluded.status_text<>'' THEN excluded.status_text ELSE matches.status_text END,winner_id=CASE WHEN ? THEN NULL ELSE COALESCE(excluded.winner_id,matches.winner_id) END,margin=CASE WHEN ? THEN NULL ELSE COALESCE(excluded.margin,matches.margin) END,victory_type=CASE WHEN ? THEN NULL ELSE COALESCE(excluded.victory_type,matches.victory_type) END""",
                (
                    m["id"],
                    m["description"],
                    m["teams"][0]["teamId"],
                    m["teams"][1]["teamId"],
                    vid,
                    m["date"],
                    m["format"],
                    m["status"],
                    m["status_text"],
                    "rapidapi-cricbuzz-v1",
                    m["winner_id"],
                    m["margin"],
                    m["victory_type"],
                    explicitly_no_winner(m["status_text"]),
                    explicitly_no_winner(m["status_text"]),
                    explicitly_no_winner(m["status_text"]),
                ),
            )
        snapshot(c, f"matches/{category}", payload)
    return matches


def ingest_scorecard(path, match_id, payload):
    with connect(path) as c:
        teams = dict(
            c.execute(
                "SELECT t.name,t.id FROM teams t JOIN matches m ON t.id IN (m.team1_id,m.team2_id) WHERE m.id=?",
                (match_id,),
            ).fetchall()
        )
        cards = normalize_scorecard(payload, teams)
        if c.execute("SELECT 1 FROM metadata WHERE key='seed_version'").fetchone():
            raise ValueError("Provider ingestion requires a separate, unseeded live database.")
        for card in cards:
            c.execute(
                "INSERT INTO innings(match_id,number,team_id,total_runs,wickets,balls) VALUES(?,?,?,?,?,?) ON CONFLICT(match_id,number) DO UPDATE SET total_runs=excluded.total_runs,wickets=excluded.wickets,balls=excluded.balls",
                (
                    match_id,
                    card["number"],
                    card["bat_team"],
                    card["runs"],
                    card["wickets"],
                    card["balls"],
                ),
            )
            iid = c.execute(
                "SELECT id FROM innings WHERE match_id=? AND number=?", (match_id, card["number"])
            ).fetchone()[0]
            # Entire innings is a provider snapshot; replace its detail atomically.
            c.execute("DELETE FROM batting WHERE innings_id=?", (iid,))
            c.execute("DELETE FROM bowling WHERE innings_id=?", (iid,))
            for kind, team in [("batters", card["bat_team"]), ("bowlers", card["bowl_team"])]:
                for p in card[kind]:
                    c.execute(
                        "INSERT INTO players(full_name,country,role,batting_style,bowling_style,source,external_id) VALUES(?,?,'Unknown','Unknown','Unknown',?,?) ON CONFLICT(external_id) DO UPDATE SET full_name=CASE WHEN players.role='Unknown' THEN excluded.full_name ELSE players.full_name END",
                        (p["name"], "Unknown", "rapidapi-cricbuzz-v1", p["id"]),
                    )
                    pid = c.execute(
                        "SELECT id FROM players WHERE external_id=?", (p["id"],)
                    ).fetchone()[0]
                    c.execute(
                        "INSERT OR IGNORE INTO participants VALUES(?,?,?)", (match_id, pid, team)
                    )
                    if kind == "batters" and p.get("did_not_bat"):
                        continue
                    if kind == "batters":
                        c.execute(
                            "INSERT INTO batting VALUES(?,?,?,?,?,?)",
                            (iid, pid, p["position"], p["runs"], p["balls"], p["dismissed"]),
                        )
                    else:
                        c.execute(
                            "INSERT INTO bowling VALUES(?,?,?,?,?)",
                            (iid, pid, p["balls"], p["runs"], p["wickets"]),
                        )
        if cards:
            first = min(cards, key=lambda card: card["number"])
            if first["number"] == 1:
                c.execute(
                    "UPDATE matches SET batting_first_id=? WHERE id=?",
                    (first["bat_team"], match_id),
                )
        team_records = [{"teamName": name, "teamId": tid} for name, tid in teams.items()]
        result_status = payload.get("status", "")
        winner, margin, victory_type = result_fields(result_status, team_records)
        if payload.get("ismatchcomplete") is True or winner is not None:
            c.execute("UPDATE matches SET status='Complete' WHERE id=?", (match_id,))
            if result_status:
                c.execute("UPDATE matches SET status_text=? WHERE id=?", (result_status, match_id))
            if winner is not None or explicitly_no_winner(result_status):
                c.execute(
                    "UPDATE matches SET winner_id=?,margin=?,victory_type=? WHERE id=?",
                    (winner, margin, victory_type, match_id),
                )
        snapshot(c, f"scorecard/{match_id}", payload)
    return cards
