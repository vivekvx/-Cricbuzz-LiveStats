# Verification report

Completed locally on 24 October 2026 using Python 3.11, SQLite, Streamlit 1.50.0, pandas 2.3.3 and requests 2.32.5 on macOS.

## Automated verification

Final full run: **118 passed in 2.68 seconds** using `.venv/bin/python -m pytest -q`.

- Every Q1–Q25 has an individual expected-answer test: rows, totals, means, eligibility, ranks or classes, rather than only checking execution.
- All 25 also run against an empty database and return empty results gracefully.
- Additional tests cover future dates and date-window boundaries, strict score thresholds, minimum balls, multiple Test innings without duplicate match counts, canonical team-pair direction, insufficient partnerships/quarters, Good/Average/Poor and declining/stable classifications.
- Ranking checks independently calculate weighted points, protect non-bowlers from an invented bowling bonus, and retain fielding-only performers.
- Arithmetic tests independently verify cricket overs, batting/strike/economy/win formulas, division by zero and population standard deviation.
- Database tests check foreign keys, rollback, repeatable initialization/seeding, SQL-only fixture loading and negative-count constraints.
- CRUD tests verify create/read/update/delete persistence, duplicate validation, protected referenced players, batting/bowling updates and correct-team eligibility.
- API tests use labeled synthetic contract fixtures for parsing, retry bounds, timeouts, missing keys, unauthorized/rate-limit/server/schema failures, input validation, idempotent ingestion, provenance, career snapshot separation and international/domestic T20 classification.
- SQL security tests reject writes, DDL, PRAGMA, ATTACH, extension loading, multiple statements and write CTEs; valid read CTEs work. Row limits and bounded recursive-query execution are tested.
- Streamlit AppTest checks all five pages, live missing-key state without sample fallback, SQL execution/rejection, persisted create forms and batting/bowling management forms.

Static verification: `ruff check .` passed; `ruff format --check .` reported all 46 Python files formatted. No test or lint failure remains in the final run.

## Actual browser verification

`scripts/record_demo.py` drove installed Google Chrome through 13 stages. It captured Home, synthetic Match centre and innings cards, ODI player statistics, beginner/intermediate/advanced SQL, destructive SQL rejection and the complete player CRUD lifecycle. The recorder also checked the database after creation, update and deletion. Browser page errors: **0**. Stage screenshots are in `docs/demo_frames/` and machine-readable recording evidence is in `docs/demo_recording.json`.

The browser recording was converted to `docs/demo.mp4`. FFprobe confirmed **H.264, 1440×1000, 41.64 seconds**, 1,758,676 bytes. It is a silent recording of actual UI interactions, not a mockup or a slideshow.

## Authenticated follow-up verification

A user-provided key was subsequently configured privately and authenticated requests succeeded for live matches, a current scorecard, player profile and batting/bowling career tables. Eight real provider-listed matches, two innings, 15 batting rows, 12 bowling rows and six career format/discipline snapshots were stored in the separate live database. Current scorecard regression tests cover the captured response, team resolution, repeated ingestion, did-not-bat rows and dismissal status; nullable bowling styles and provider keeper-role mapping are also tested. See LIVE_VERIFICATION.md for exact scope. Exact plan entitlements, API quotas and complete historical coverage remain unverified.

## Subsequent compliance audit

See COMPLIANCE_AUDIT.md for corrected Q12/Q16/Q23/Q25 semantics and five new regression cases. The current final run has 92 passing tests.

## Community Cloud preparation

The current run has 97 passing tests, including secrets configuration, hosted-storage disclosure and concurrent first-visitor seeding. Dependency compatibility (`pip check`) also passes. See STREAMLIT_DEPLOYMENT.md for repository values and the Ubuntu GitHub Actions verification.

## Hosted missing-key recovery

The current run has 98 passing tests. The missing-key Home state now explains why live counts are zero, links the owner to Cloud Secrets instructions, and provides an explicit one-click switch to the seeded demo with its reference date. AppTest verifies the recovered 60-match/eight-player/25-question state.

## Cross-page data source persistence

The source selector now stores its value independently of page-specific widgets. A multipage regression switches Live API through Home and all four modules, then switches explicitly to Sample Data and verifies that choice survives navigation. Current full suite: 99 passed.

## Live-data accuracy audit

Ten authenticated requests captured three match lists, T20I/ODI/Test scorecards, match information and one player’s profile/career tables. The isolated import passed 268 checks across 86 unique matches, 66 players and seven innings. Totals/results were cross-checked against indexed Cricbuzz/ICC listings. See LIVE_DATA_AUDIT.md for evidence and limits, including an upstream 0.01 strike-rate discrepancy.

New regressions cover real three-format cards, domestic/unofficial/warm-up exclusion, explicit result parsing, outcome retention under incomplete/cached refreshes, saved-data migration, timestamps, missing-metadata disclosures and legacy did-not-bat rows. Independent review identified result-erasure and T20 warm-up classification defects; both were corrected before the final 112-test run.

## Hosted Python 3.14 chart compatibility

Browser verification exposed a crash when Streamlit’s bar-chart wrapper imported Altair’s schema on the deployed Python 3.14 runtime. The player chart now uses Streamlit’s direct Vega-Lite specification, preserving the bar chart and tooltip without importing Altair. A regression blocks Altair imports and verifies the chart and comparison section still render. CI now tests Python 3.11 and 3.14.

## Repeated empty SQL results

See SQL_DATA_COVERAGE.md. Hosted SQL confirmed nine listed matches but only one imported scorecard. All 25 statements were checked locally: 15 live queries were empty, while all 25 sample queries returned rows. Five new regressions cover explanatory empty states, actual Q9/Q16 evidence, all-query status/error distinction and explicit sample switching. This corrects the earlier distinction between calculation correctness and historical data readiness.
