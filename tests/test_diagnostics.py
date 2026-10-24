"""Regression for identical empty messages hiding insufficient live history."""

import json
import sqlite3
from pathlib import Path
from analytics.diagnostics import audit_questions, dataset_summary, empty_explanation
from database.connection import initialize, connect
from services.ingestion import ingest_matches, ingest_scorecard


def one_live_card(path):
    initialize(path)
    case = json.loads((Path(__file__).parent / "fixtures/audited_scorecards.json").read_text())[0]
    ingest_matches(
        path,
        {
            "typeMatches": [
                {
                    "matchType": "International",
                    "seriesMatches": [
                        {"seriesAdWrapper": {"matches": [{"matchInfo": case["match"]}]}}
                    ],
                }
            ]
        },
    )
    ingest_scorecard(path, case["match"]["matchId"], case["card"])
    with connect(path) as conn:
        conn.execute("UPDATE players SET role='All-rounder' WHERE external_id=8808")


def test_one_scorecard_cannot_answer_career_or_yearly_thresholds(tmp_path):
    path = tmp_path / "live.sqlite3"
    one_live_card(path)
    assert dataset_summary(path)["scorecard_matches"] == 1
    checks = audit_questions(path, "2026-10-24")
    assert len(checks) == 25
    assert checks[8]["Rows"] == checks[15]["Rows"] == 0
    assert checks[6]["Rows"] == 1
    q9 = empty_explanation(path, 9, "2026-10-24", "Live API")
    q16 = empty_explanation(path, 16, "2026-10-24", "Live API")
    assert "highest stored runs per format: 11" in q9
    assert "highest stored wickets per format: 0" in q9
    assert "single eligible year: 1" in q16
    assert "requires at least 5" in q16
    assert q9 != q16
    assert "not evidence that no real player" in q9


def test_sample_has_nonempty_results_for_every_assignment_question(db):
    checks = audit_questions(db, "2026-10-24")
    assert len(checks) == 25
    assert all(r["Status"] == "Has results" and r["Rows"] > 0 for r in checks)


def test_audit_distinguishes_query_error_from_no_matches(db, monkeypatch):
    import analytics.diagnostics as diagnostics

    original = diagnostics.execute

    def fail_one(path, number, as_of):
        if number == 9:
            raise sqlite3.OperationalError("test query error")
        return original(path, number, as_of)

    monkeypatch.setattr(diagnostics, "execute", fail_one)
    checks = audit_questions(db, "2026-10-24")
    assert checks[8]["Rows"] is None
    assert checks[8]["Status"] == "Query failed: test query error"
    assert checks[15]["Status"] == "Has results"
