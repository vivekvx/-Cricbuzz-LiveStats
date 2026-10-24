# 🏏 Cricbuzz LiveStats

A complete local Python/Streamlit cricket analytics assignment: five pages, 25 executable SQLite questions, persistent player and match-statistic CRUD, API ingestion and a reproducible synthetic-data demonstration.

**Status:** Both sample mode and authenticated API mode have been verified locally. The provided key is configured privately in the ignored `.env` file. Live verification imported eight provider-listed matches, a two-innings scorecard, and a player profile with career tables. The submission ZIP excludes credentials. See [API verification](docs/LIVE_VERIFICATION.md).

## Features

- Home with database status, documentation and module navigation.
- Match centre with manual API refresh, team scores, venue/format/status, innings, batting and bowling cards; clearly labeled synthetic demonstration mode.
- Format-filtered most runs, highest scores, most wickets, batting averages and economies; charts, comparisons and CSV export.
- All 25 exact assignment questions with difficulty, SQL, explanations, assumptions, results and CSV export; a restricted read-only SQL editor.
- Player create/search/update/delete and batting/bowling statistics create/read/update/delete with validation, deletion confirmation and persistent transactions.
- Separate sample and provider databases; normalized scorecards and payload provenance; no automatic API polling.

## Prerequisites and setup

Python **3.11** (tested), pip, and a local browser. SQLite is built into Python; no database server is needed.

```bash
cd /Users/vivek/Projects/cricbuzz_livestats
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m database.seed
streamlit run main.py
```

Open the local address printed by Streamlit, normally http://localhost:8501. Database initialization also runs automatically on page load. For SQL-only loading, initialize with `database/schema.sql` and then execute `data/sample_data/seed.sql` with foreign keys enabled. The deterministic seed contains 60 fictional fixtures and eight fictional players; its reference date is **2026-10-24**. This avoids old demonstrations silently losing date-window results. Change the sidebar reference date to explore other windows.

Set `RAPIDAPI_KEY` in `.env` or `.streamlit/secrets.toml` to use the provider. Base URL and host are configurable through the variables in [.env.example](.env.example). `CRICBUZZ_DATA_DIR` optionally changes database storage. Keys are never displayed. See [API_SETUP](docs/API_SETUP.md) for provider/version/pricing research and exact verification limits.

## Deploy to Streamlit Community Cloud

The repository is prepared for Community Cloud. Use repository `vivekvx/-Cricbuzz-LiveStats`, branch `main`, entry point `main.py`, and select Python **3.11** under Advanced settings. Put the real API key in Cloud **Secrets**, using `.streamlit/secrets.toml.example` as a template; never commit the actual secrets file. Sample Data works without a key.

See [STREAMLIT_DEPLOYMENT.md](docs/STREAMLIT_DEPLOYMENT.md) for exact setup, validation and sharing settings. Hosted SQLite data is temporary and shared across viewers; use a private assignment demo and export important results. A persistent external database would be needed for durable multi-user production storage.

## Navigate and demonstrate

Start at Home. Choose Sample Data or Live API in the sidebar; every module uses that same selected source. In Sample Data, Match centre shows completed synthetic fixtures rather than claiming they are live. Player statistics reads the same stored scorecards as SQL analytics. In SQL analytics choose a difficulty and question, inspect SQL, then execute. Export results using Download CSV. Manage records provides persistent forms; duplicate names and referenced-player deletion are rejected.

In Live API, explicitly refresh a match list and fetch a scorecard. The player page can fetch a profile and career tables by provider ID. API totals and scorecard totals are displayed separately to prevent double counting. Some analytics require historical/winner/toss/fielding/series facts that list endpoints do not provide; empty/incomplete live results are disclosed rather than replaced with samples.

## Project structure

```text
main.py                   Home entry point
ui.py                     Shared Streamlit page controllers
config.py                 Environment/secrets and mode paths
pages/                    Four functional module entry points
api/                      Client, match and player endpoint adapters
database/                 Schema, seed, connections and CRUD repository
utils/db_connection.py    Assignment-compatible connection re-export
services/                 Validation/normalization and atomic ingestion
analytics/sql/q01..25.sql  Actual SQL solutions
analytics/                Question registry, execution and arithmetic
data/sample_data/        Synthetic dataset provenance manifest
tests/                   Expected-value, security, API and UI tests
docs/                    Assignment, SQL, schema, API and demonstration guides
scripts/                 Browser walkthrough recorder
```

## Verification

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
ruff check .
ruff format --check .
```

Tests check expected answers for every question, independent cricket arithmetic, repeated initialization, foreign keys, CRUD persistence, duplicate handling, API retries/failures/schema parsing, mode separation, read-only SQL restrictions and all five Streamlit pages. Synthetic API fixtures are labeled; captured public scorecard fixtures have explicit provenance. See [TEST_REPORT](docs/TEST_REPORT.md) for the actual completed run.

The custom SQL connection opens the database with SQLite mode=ro, denies unauthorized operations through SQLite's authorizer, caps returned rows at 5,000 and bounds execution to roughly ten million VM operations. These restrictions also apply to registered queries. It is an academic application without authentication; use private app sharing on Community Cloud because CRUD records and API quota are shared.

## Deliverables

- [25 SQL solutions and assumptions](docs/SQL_SOLUTIONS.md)
- [Database relationships](docs/DATABASE_SCHEMA.md)
- [API setup and research](docs/API_SETUP.md)
- [Demo script and recording instructions](docs/DEMO_GUIDE.md)
- [Requirements traceability](docs/REQUIREMENTS_CHECKLIST.md)
- [Latest compliance audit and remaining limits](docs/COMPLIANCE_AUDIT.md)
- [Live data accuracy audit](docs/LIVE_DATA_AUDIT.md)
- [Original assignment text](docs/ASSIGNMENT_SOURCE.txt), extracted completely from the supplied Cricbuzz.docx
- `docs/demo.mp4`: actual browser walkthrough, generated by scripts/record_demo.py and local video conversion.

## Troubleshooting and limitations

- Missing key: use Sample Data or configure RAPIDAPI_KEY. No automatic source fallback occurs.
- 401/403: verify provider subscription and v1 version. 429: wait as directed by the provider. Unexpected schemas are rejected; both observed legacy and current lowercase scorecard structures are supported.
- Empty SQL result: check selected source, available data, date reference and query eligibility thresholds. Stored provider scorecards are not a complete historical database.
- Undefined average: a player with no dismissals/wickets has NULL rather than a fabricated average.
- Duplicate player: names are unique case-insensitively. Same-name real players would require a richer identity model.
- Delete blocked: remove dependent records intentionally first; the app does not cascade-delete a player's history.
- SQL rejected: only a single read query is allowed; PRAGMA, ATTACH, writes and extension/file functions are forbidden.
- Database locked: close other database writers and retry. The app uses short-lived transactions and a ten-second connection timeout.
- Seed is intentionally artificial for transparent oracles, not a cricket match simulator. Synthetic result margins are fixture inputs, not inferred from displayed batting totals. Only four batters/two bowlers per side are included. No sample statistic represents a real cricketer.
- Partnerships are adjacent-position **combined-score proxies**, not verified stands. See the visible SQL assumptions.
- Demo video is a silent screen recording; the accompanying script supplies narration. Authenticated live-provider access is documented separately in docs/LIVE_VERIFICATION.md.

For repeated empty live SQL results, see [SQL data coverage investigation](docs/SQL_DATA_COVERAGE.md). SQL Analytics now shows imported-data counts and can check all 25 question results without API calls. Use its explicit sample-data switch for the full fictional assignment demo.
