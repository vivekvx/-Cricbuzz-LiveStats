"""Audit captured provider JSON offline, including arithmetic and persisted results."""

from pathlib import Path
import json
import tempfile
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database.connection import initialize, read_query, connect
from services.ingestion import ingest_matches, ingest_scorecard
from services.player_service import fetch_player
from analytics.queries import execute
from database import repository

if len(sys.argv) != 2:
    raise SystemExit("Usage: python scripts/audit_captured.py /path/to/captured-responses")
root = Path(sys.argv[1])
report = {
    "checked_at": datetime.now(timezone.utc).isoformat(),
    "list_records": {},
    "checks": [],
    "cards": [],
}


def check(name, condition):
    assert condition, name
    report["checks"].append(name)


with tempfile.TemporaryDirectory() as temp:
    db = Path(temp) / "audit.sqlite3"
    initialize(db)
    all_ids = set()
    for category in ("live", "recent", "upcoming"):
        payload = json.loads((root / (category + ".json")).read_text())
        normalized = ingest_matches(db, payload, category)
        report["list_records"][category] = len(normalized)
        all_ids.update(m["id"] for m in normalized)
        for item in normalized:
            row = read_query(db, "SELECT * FROM matches WHERE id=:id", {"id": item["id"]})[0]
            check(
                f"{category}/{item['id']} teams, date, format, status",
                row["team1_id"] == item["teams"][0]["teamId"]
                and row["team2_id"] == item["teams"][1]["teamId"]
                and row["match_date"] == item["date"]
                and row["format"] == item["format"]
                and row["status"] == item["status"],
            )
    check(
        "listing duplicates do not duplicate matches",
        len(read_query(db, "SELECT * FROM matches")) == len(all_ids),
    )
    report["unique_matches"] = len(all_ids)
    for mid in (161201, 170727, 147931):
        raw = json.loads((root / f"card_{mid}.json").read_text())
        cards = ingest_scorecard(db, mid, raw)
        before = {
            t: read_query(db, f"SELECT COUNT(*) n FROM {t}")[0]["n"]
            for t in ("innings", "batting", "bowling", "participants")
        }
        ingest_scorecard(db, mid, raw)
        check(
            f"{mid} repeated scorecard import is idempotent",
            before == {t: read_query(db, f"SELECT COUNT(*) n FROM {t}")[0]["n"] for t in before},
        )
        for source, card in zip(raw["scorecard"], cards):
            tag = f"{mid}/innings-{card['number']}"
            check(
                tag + " batting plus extras equals innings runs",
                sum(b["runs"] for b in source["batsman"]) + source["extras"]["total"]
                == source["score"],
            )
            check(
                tag + " bowler legal balls equals innings legal balls",
                sum(b["balls"] for b in source["bowler"]) == source["ballnbr"],
            )
            check(
                tag + " bowling conceded plus non-bowler extras equals innings runs",
                sum(b["runs"] for b in source["bowler"])
                + sum(source["extras"].get(k, 0) for k in ("legbyes", "byes", "penalty"))
                == source["score"],
            )
            check(
                tag + " dismissals equal wickets",
                sum(b["dismissed"] for b in card["batters"]) == source["wickets"],
            )
            innings = read_query(
                db,
                "SELECT * FROM innings WHERE match_id=:mid AND number=:number",
                {"mid": mid, "number": card["number"]},
            )[0]
            check(
                tag + " stored innings matches provider",
                innings["total_runs"] == source["score"]
                and innings["wickets"] == source["wickets"]
                and innings["balls"] == source["ballnbr"],
            )
            bats = read_query(
                db,
                "SELECT b.*,p.external_id FROM batting b JOIN players p ON p.id=b.player_id WHERE innings_id=:id ORDER BY position",
                {"id": innings["id"]},
            )
            expected = [b for b in card["batters"] if not b["did_not_bat"]]
            check(
                tag + " DNB players excluded and batsman values exact",
                [(b["external_id"], b["runs"], b["balls"], b["dismissed"]) for b in bats]
                == [(b["id"], b["runs"], b["balls"], b["dismissed"]) for b in expected],
            )
            bowls = read_query(
                db,
                "SELECT b.*,p.external_id FROM bowling b JOIN players p ON p.id=b.player_id WHERE innings_id=:id ORDER BY p.external_id",
                {"id": innings["id"]},
            )
            check(
                tag + " bowler values exact",
                [(b["external_id"], b["runs"], b["balls"], b["wickets"]) for b in bowls]
                == sorted((b["id"], b["runs"], b["balls"], b["wickets"]) for b in card["bowlers"]),
            )
        report["cards"].append({"id": mid, "innings": len(cards), "result": raw["status"]})
    for row in read_query(db, "SELECT * FROM career"):
        bats = read_query(
            db,
            "SELECT runs,balls,dismissed FROM batting_facts WHERE player_id=:pid AND format=:fmt",
            {"pid": row["player_id"], "fmt": row["format"]},
        )
        if bats:
            runs = sum(b["runs"] for b in bats)
            balls = sum(b["balls"] for b in bats)
            outs = sum(b["dismissed"] for b in bats)
            check(
                f"career/{row['player_id']}/{row['format']} batting rates",
                row["runs"] == runs
                and row["batting_average"] == (runs / outs if outs else None)
                and row["strike_rate"] == (100 * runs / balls if balls else None),
            )
        bowls = read_query(
            db,
            "SELECT runs,balls,wickets FROM bowling_facts WHERE player_id=:pid AND format=:fmt",
            {"pid": row["player_id"], "fmt": row["format"]},
        )
        if bowls:
            runs = sum(b["runs"] for b in bowls)
            balls = sum(b["balls"] for b in bowls)
            w = sum(b["wickets"] for b in bowls)
            check(
                f"career/{row['player_id']}/{row['format']} bowling rates",
                row["wickets"] == w
                and row["economy"] == (6 * runs / balls if balls else None)
                and row["bowling_average"] == (runs / w if w else None),
            )

    class Captured:
        def get(self, path):
            kind = path.rsplit("/", 1)[-1]
            return json.loads(
                (
                    root / f"player_{kind if kind in ('batting', 'bowling') else 'profile'}.json"
                ).read_text()
            )

    fetch_player(db, Captured(), 8808)
    for record in read_query(db, "SELECT * FROM player_career_stats"):
        raw = json.loads((root / f"player_{record['discipline']}.json").read_text())
        idx = next(i for i, h in enumerate(raw["headers"]) if h.upper() == record["format"].upper())
        expected = {r["values"][0]: r["values"][idx] for r in raw["values"]}
        check(
            f"API career table {record['format']}/{record['discipline']} stored verbatim",
            json.loads(record["payload"]) == expected,
        )
    for number in range(1, 26):
        output = execute(db, number, "2026-10-24")
        check(
            f"Q{number} on real imported data returns records or explicit empty result",
            isinstance(output, list),
        )
    pid = repository.create_player(
        db, "Audit Temporary Learner", "India", "Batsman", "Right-hand bat", "None"
    )
    repository.update_player(
        db, pid, "Audit Updated Learner", "Australia", "Bowler", "Right-hand bat", "Spin"
    )
    check(
        "CRUD update persisted in isolated real-data database",
        repository.players(db, "Audit Updated")[0]["country"] == "Australia",
    )
    repository.delete_player(db, pid)
    check(
        "CRUD delete persisted in isolated real-data database",
        repository.players(db, "Audit Updated") == [],
    )
    with connect(db) as c:
        check("no foreign-key violations", c.execute("PRAGMA foreign_key_check").fetchall() == [])
    report["stored_rows"] = {
        t: read_query(db, f"SELECT COUNT(*) n FROM {t}")[0]["n"]
        for t in ("matches", "players", "innings", "batting", "bowling")
    }
    report["checks_passed"] = len(report["checks"])
    report["result"] = "pass"
(root / "audit_results.json").write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != "checks"}, indent=2))
