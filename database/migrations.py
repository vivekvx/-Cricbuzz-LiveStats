"""Repair old live classifications using saved provider evidence, once."""

import json
from services.normalization import normalize_matches
from api.client import ApiError
from services.results import explicitly_no_winner


def apply(conn):
    if conn.execute("SELECT 1 FROM metadata WHERE key='live_normalization_v3'").fetchone():
        return
    if not conn.execute("SELECT 1 FROM metadata WHERE key='seed_version'").fetchone():
        for row in conn.execute(
            "SELECT payload FROM api_snapshots WHERE endpoint LIKE 'matches/%' ORDER BY fetched_at"
        ):
            try:
                matches = normalize_matches(json.loads(row["payload"]))
            except (ValueError, ApiError):
                continue
            for match in matches:
                conn.execute(
                    "UPDATE matches SET format=? WHERE id=? AND source='rapidapi-cricbuzz-v1'",
                    (match["format"], match["id"]),
                )
                if match["winner_id"] is not None or explicitly_no_winner(match["status_text"]):
                    conn.execute(
                        "UPDATE matches SET winner_id=?,margin=?,victory_type=? WHERE id=? AND source='rapidapi-cricbuzz-v1'",
                        (match["winner_id"], match["margin"], match["victory_type"], match["id"]),
                    )
    conn.execute("INSERT INTO metadata VALUES('live_normalization_v3','1')")
