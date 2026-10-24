"""Shared presentation and page controllers for the five-page dashboard."""

from datetime import date
import json
import sqlite3
import pandas as pd
import streamlit as st
from analytics.calculations import balls_to_overs, provider_overs_display
from analytics.queries import execute
from analytics.query_registry import ASSUMPTIONS, QUESTIONS
from analytics.validations import ROLES
from api.client import ApiError, Client
from api.matches import match_list, scorecard
from config import ROOT, api_key, database_path, cloud_deployment
from database import repository as repo
from database.connection import initialize, read_query
from database.seed import DEMO_DATE, seed
from services.ingestion import ingest_matches, ingest_scorecard
from services.player_service import fetch_player


def start_demo():
    """Explicitly select synthetic data and its reproducible reference date."""
    st.session_state["data_mode"] = "Sample Data"
    st.session_state["as_of_Sample Data"] = date.fromisoformat(DEMO_DATE)


def setup(title):
    """Initialize the selected mode and return its database and reference date."""
    st.set_page_config(page_title=f"{title} · Cricbuzz LiveStats", page_icon="🏏", layout="wide")
    st.markdown(
        """<style>
    .stApp {background:#f6f8f7;color:#142c29;}
    h1,h2,h3 {letter-spacing:-0.03em;}
    [data-testid="stMetric"] {background:white;border:1px solid #dce5e1;border-radius:12px;padding:18px;}
    .hero {background:#123d35;color:#fff;padding:32px;border-radius:18px;margin-bottom:24px;}
    .hero p {color:#c9e4d8;max-width:760px;font-size:18px;}
    .eyebrow {color:#9de3bc;letter-spacing:.16em;font-size:12px;font-weight:700;}
    </style>""",
        unsafe_allow_html=True,
    )
    st.sidebar.title("🏏 LiveStats")
    mode = st.sidebar.selectbox("Data source", ["Sample Data", "Live API"], key="data_mode")
    path = database_path(mode)
    if mode == "Sample Data":
        seed(path)
        st.sidebar.warning("SYNTHETIC DATA · Fictional players and fixtures")
        st.sidebar.caption(f"Demo reference date: {DEMO_DATE}")
    else:
        initialize(path)
        st.sidebar.info("LIVE API · Provider records only")
        st.sidebar.caption("Key configured" if api_key() else "API key missing")
        if not api_key():
            st.warning(
                "Live API is not connected: this deployment has no API key. Its live database starts empty; your local key and data are not copied to the hosted app."
            )
            st.button("Start demo with sample data", on_click=start_demo, type="primary")
            st.caption(
                "Demo data is clearly labeled, requires no key and includes results for all 25 SQL questions. It is never presented as live cricket."
            )
            with st.expander("App owner: enable live data on Streamlit Cloud"):
                st.write(
                    "Open Manage app → Settings → Secrets. Add RAPIDAPI_KEY and save. Then open Live Matches and press Refresh matches, select a match and fetch its detailed scorecard."
                )
                st.code(
                    'RAPIDAPI_KEY = "your_actual_key"\nDEPLOYMENT_ENV = "community-cloud"',
                    language="toml",
                )
    as_of = st.sidebar.date_input(
        "Analytics reference date",
        value=date.fromisoformat(DEMO_DATE) if mode == "Sample Data" else date.today(),
        key=f"as_of_{mode}",
    ).isoformat()
    st.sidebar.caption("Manual refresh · No automatic polling")
    if cloud_deployment():
        st.sidebar.info(
            "Hosted demo: database edits are shared with other viewers and may reset. Export important results as CSV."
        )
    return path, mode, as_of


def table(rows, key="table"):
    """Render an exportable table or an honest empty state."""
    if not rows:
        st.info("No records meet these conditions in the selected database.")
        return
    frame = pd.DataFrame(rows)
    st.dataframe(frame, hide_index=True, width="stretch")
    st.download_button(
        "Download CSV",
        frame.to_csv(index=False).encode(),
        f"{key}.csv",
        "text/csv",
        key=f"csv_{key}",
    )


def home():
    path, mode, as_of = setup("Home")
    st.markdown(
        """<div class="hero"><div class="eyebrow">CRICKET INTELLIGENCE / SQL LAB</div>
    <h1>Cricbuzz LiveStats</h1><p>Follow the match. Explore the numbers. Understand the game.</p>
    <p>A Python and SQLite workspace for scorecards, player comparisons and 25 cricket analytics questions.</p></div>""",
        unsafe_allow_html=True,
    )
    counts = read_query(
        path,
        "SELECT (SELECT COUNT(*) FROM matches) matches,(SELECT COUNT(*) FROM players) players,(SELECT COUNT(*) FROM batting) batting_innings",
    )[0]
    for col, (label, value) in zip(
        st.columns(4),
        [
            ("Matches", counts["matches"]),
            ("Players", counts["players"]),
            ("Batting innings", counts["batting_innings"]),
            ("SQL questions", 25),
        ],
    ):
        col.metric(label, value)
    if mode == "Live API" and counts["matches"] == 0 and api_key():
        st.info(
            "Your API key is configured. Load the first match snapshot in Match centre; the hosted database is separate from your computer."
        )
        st.page_link("pages/1_Live_Matches.py", label="Load live matches", icon="🏏")
    st.subheader("Your cricket workspace")
    a, b = st.columns(2)
    with a:
        st.page_link("pages/1_Live_Matches.py", label="Match centre", icon="🏏")
        st.write(
            "Browse scores, venue details and full batting and bowling cards. Refresh the API on demand."
        )
        st.page_link("pages/2_Top_Player_Stats.py", label="Player statistics", icon="📊")
        st.write("Filter by format, compare players and explore batting and bowling leaders.")
    with b:
        st.page_link("pages/3_SQL_Analytics.py", label="SQL analytics", icon="🔎")
        st.write("Run all 25 assignment questions, inspect their SQL and export results.")
        st.page_link("pages/4_CRUD_Operations.py", label="Manage records", icon="🛠️")
        st.write("Create, search, edit and delete persistent player and match-statistic records.")
    st.success(f"Database initialized · {mode} · schema version 1")
    st.caption(f"Current analytics reference date: {as_of}")
    if mode == "Sample Data":
        st.warning(
            "Every sample player, fixture and performance is explicitly synthetic. Match cards are demonstrations, not live cricket scores."
        )
    st.subheader("How data moves")
    st.write(
        "Cricbuzz Cricket REST API → validated Python ingestion → SQLite storage → SQL analytics → Streamlit. Provider snapshots preserve provenance. Sample and API databases are physically separate."
    )
    st.write(
        "Choose a source in the sidebar, open a module, then use its controls. In Live API mode, fetch matches and scorecards before expecting scorecard-based analytics. Store a subscribed key in `.env` or Streamlit secrets."
    )
    with st.expander("Documentation and project structure"):
        st.code(
            "main.py\napi/  services/  database/  analytics/sql/\npages/  tests/  docs/  data/sample_data/"
        )
        for name in [
            "README.md",
            "docs/API_SETUP.md",
            "docs/SQL_SOLUTIONS.md",
            "docs/DEMO_GUIDE.md",
        ]:
            file = ROOT / name
            if file.exists():
                st.download_button(name, file.read_text(), file.name, key=name)


@st.cache_data(ttl=120, show_spinner=False)
def cached_matches(key, category):
    return match_list(Client(key=key), category)


@st.cache_data(ttl=120, show_spinner=False)
def cached_card(key, match_id):
    return scorecard(Client(key=key), match_id)


def match_centre():
    path, mode, _ = setup("Match centre")
    st.title("Match centre")
    st.caption("Scores, venues and innings details · refresh on demand")
    if mode == "Live API":
        category = st.selectbox("Match list", ["live", "recent", "upcoming"])
        if st.button("Refresh matches", type="primary"):
            try:
                cached_matches.clear()
                ingest_matches(path, cached_matches(api_key(), category), category)
                st.success("Provider snapshot stored.")
            except (ApiError, ValueError, sqlite3.Error) as exc:
                st.error(str(exc))
        snapshots = read_query(
            path,
            "SELECT payload,fetched_at FROM api_snapshots WHERE endpoint=:endpoint",
            {"endpoint": f"matches/{category}"},
        )
        if not snapshots:
            st.info(
                "No provider snapshot yet. Use Refresh matches. API failures never fall back to sample scores."
            )
            return
        st.caption(
            f"Last successful fetch: {snapshots[0]['fetched_at']} · saved snapshot may be stale"
        )
        from services.normalization import normalize_matches

        try:
            normalized = normalize_matches(json.loads(snapshots[0]["payload"]))
        except ApiError as exc:
            st.error(str(exc))
            return
        if not normalized:
            st.info("Provider returned an empty match list.")
            return
        ids = [m["id"] for m in normalized]
        for match in normalized:
            with st.container(border=True):
                st.subheader(" vs ".join(t["teamName"] for t in match["teams"]))
                st.write(
                    f"{match['format']} · {match['venue'].get('ground', 'Venue unavailable')} · {match['venue'].get('city', '')}"
                )
                st.write(match["status_text"] or match["status"])
                for side, scores in match["scores"].items():
                    if isinstance(scores, dict):
                        for ino, value in scores.items():
                            if isinstance(value, dict):
                                st.write(
                                    f"{match['teams'][0 if side == 'team1Score' else 1]['teamName']} {ino}: {value.get('runs', '—')}/{value.get('wickets', '—')} ({provider_overs_display(value.get('overs', '—'))} overs)"
                                )
        selected = st.selectbox("Match for scorecard", ids)
        if st.button("Fetch detailed scorecard"):
            try:
                cached_card.clear()
                ingest_scorecard(path, selected, cached_card(api_key(), selected))
                st.success("Scorecard stored. Batting and bowling tables appear below.")
            except (ApiError, ValueError, sqlite3.Error) as exc:
                st.error(str(exc))
    else:
        st.warning("SYNTHETIC MATCH DEMONSTRATION · These completed fixtures are not live scores.")
        matches = read_query(
            path,
            "SELECT m.id,m.description,m.format,m.match_date,t1.name team1,t2.name team2,m.status_text,v.name venue,v.city FROM matches m JOIN teams t1 ON t1.id=m.team1_id JOIN teams t2 ON t2.id=m.team2_id LEFT JOIN venues v ON v.id=m.venue_id ORDER BY match_date DESC,m.id DESC LIMIT 10",
        )
        selected = st.selectbox(
            "Sample fixture",
            [m["id"] for m in matches],
            format_func=lambda mid: next(
                f"{m['description']} · {m['format']} · {m['match_date']}"
                for m in matches
                if m["id"] == mid
            ),
        )
        match = next(m for m in matches if m["id"] == selected)
        st.subheader(f"{match['team1']} vs {match['team2']}")
        st.write(f"{match['venue']} · {match['city']} · {match['status_text']}")
    innings = read_query(
        path,
        "SELECT i.*,t.name team FROM innings i JOIN teams t ON t.id=i.team_id WHERE match_id=:mid ORDER BY number",
        {"mid": selected},
    )
    if not innings:
        st.info("No detailed scorecard stored for this match.")
    for item in innings:
        st.subheader(f"Innings {item['number']} · {item['team']}")
        st.write(f"{item['total_runs']}/{item['wickets']} · {balls_to_overs(item['balls'])} overs")
        table(
            read_query(
                path,
                "SELECT p.full_name,b.position,b.runs,b.balls,b.dismissed,100.0*b.runs/NULLIF(b.balls,0) strike_rate FROM batting b JOIN players p ON p.id=b.player_id WHERE innings_id=:iid ORDER BY position",
                {"iid": item["id"]},
            ),
            f"bat_{item['id']}",
        )
        table(
            read_query(
                path,
                "SELECT p.full_name,b.balls legal_balls,b.runs,b.wickets,6.0*b.runs/NULLIF(b.balls,0) economy FROM bowling b JOIN players p ON p.id=b.player_id WHERE innings_id=:iid",
                {"iid": item["id"]},
            ),
            f"bowl_{item['id']}",
        )


def player_stats():
    path, mode, _ = setup("Player statistics")
    st.title("Player statistics")
    st.caption(
        "Career summaries below are calculated from stored scorecards; coverage may be incomplete."
    )
    if mode == "Live API":
        with st.expander("Fetch player profile and career statistics from API"):
            provider_id = st.number_input("Provider player ID", min_value=1, value=8733, step=1)
            if st.button("Fetch player statistics"):
                try:
                    fetch_player(path, Client(), provider_id)
                    st.success("Profile and career snapshots saved.")
                except (ApiError, ValueError, sqlite3.Error) as exc:
                    st.error(str(exc))
        saved = read_query(
            path,
            "SELECT p.full_name,s.format,s.discipline,s.payload,s.fetched_at FROM player_career_stats s JOIN players p ON p.id=s.player_id ORDER BY p.full_name,s.format,s.discipline",
        )
        if saved:
            st.subheader("API career snapshots")
            table(
                [
                    {
                        **{k: v for k, v in row.items() if k != "payload"},
                        **json.loads(row["payload"]),
                    }
                    for row in saved
                ],
                "api_career",
            )
    fmt = st.selectbox("Cricket format", ["All", "Test", "ODI", "T20I", "T20", "Other"])
    rows = read_query(
        path,
        'SELECT p.full_name,c.* FROM career c JOIN players p ON p.id=c.player_id WHERE :fmt="All" OR c.format=:fmt ORDER BY c.runs DESC,p.id,c.format',
        {"fmt": fmt},
    )
    if not rows:
        st.info(
            "No scorecard-based player statistics yet. Fetch a match scorecard in Match centre."
        )
        return
    df = pd.DataFrame(rows)
    metric = st.selectbox(
        "Leaderboard", ["runs", "highest", "wickets", "batting_average", "economy"]
    )
    ranked = df.sort_values(metric, ascending=metric == "economy", na_position="last")
    table(ranked.to_dict("records"), "player_leaderboard")
    chart = ranked.dropna(subset=[metric]).head(10).copy()
    chart["Player / format"] = chart["full_name"] + " / " + chart["format"]
    st.bar_chart(chart, x="Player / format", y=metric, color="#16815c")
    st.subheader("Compare players")
    names = sorted(df["full_name"].unique())
    chosen = st.multiselect("Choose players", names, default=names[:2])
    table(df[df["full_name"].isin(chosen)].to_dict("records"), "player_comparison")


def sql_analytics():
    path, _, as_of = setup("SQL analytics")
    st.title("SQL queries & analytics")
    st.caption("25 questions · inspect the SQL · execute against the current database")
    level = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
    choices = [q for q in QUESTIONS if q["level"] == level]
    number = st.selectbox(
        "Question",
        [q["id"] for q in choices],
        format_func=lambda n: f"Q{n} · {QUESTIONS[n - 1]['question'][:85]}",
    )
    q = QUESTIONS[number - 1]
    st.subheader(f"Q{number} · {level}")
    st.write(q["question"])
    for line in q["details"]:
        st.write(line)
    st.code(q["sql"], language="sql")
    st.write(q["explanation"])
    with st.expander("Definitions, thresholds and assumptions"):
        st.text(ASSUMPTIONS)
    if st.button("Execute question", type="primary"):
        try:
            table(execute(path, number, as_of), f"q{number}")
        except (sqlite3.Error, ValueError) as exc:
            st.error(f"Query could not finish: {exc}")
    st.divider()
    st.subheader("Read-only SQL workspace")
    st.caption(
        "Single read query only · 5,000-row maximum · bounded execution · :as_of parameter available"
    )
    sql = st.text_area(
        "SQL",
        "SELECT full_name, role, country FROM players ORDER BY full_name LIMIT 100;",
        height=150,
    )
    if st.button("Run read-only SQL"):
        try:
            table(read_query(path, sql, {"as_of": as_of}), "custom_sql")
        except (sqlite3.Error, ValueError) as exc:
            st.error(f"Read-only query rejected or invalid: {exc}")


def player_form(prefix, record=None):
    record = record or {}
    name = st.text_input("Full name", record.get("full_name", ""), key=f"{prefix}_name")
    country = st.text_input(
        "Country represented", record.get("country", ""), key=f"{prefix}_country"
    )
    role = st.selectbox(
        "Playing role",
        ROLES,
        index=ROLES.index(record.get("role", "Batsman"))
        if record.get("role", "Batsman") in ROLES
        else 0,
        key=f"{prefix}_role",
    )
    bat = st.text_input(
        "Batting style", record.get("batting_style", "Right-hand bat"), key=f"{prefix}_bat"
    )
    bowl = st.text_input("Bowling style", record.get("bowling_style", "None"), key=f"{prefix}_bowl")
    return name, country, role, bat, bowl


def crud():
    path, mode, _ = setup("Manage records")
    st.title("Manage records")
    st.caption(f"Changes are saved to the {mode} database.")
    action = st.radio(
        "Operation",
        ["Read / search", "Create player", "Update player", "Delete player", "Match statistics"],
        horizontal=True,
    )
    try:
        if action == "Read / search":
            table(repo.players(path, st.text_input("Search players")), "players_search")
        elif action == "Create player":
            with st.form("create_player", clear_on_submit=True):
                values = player_form("new")
                if st.form_submit_button("Create player"):
                    pid = repo.create_player(path, *values)
                    st.success(f"Player {pid} created and saved.")
        elif action in ("Update player", "Delete player"):
            records = repo.players(path)
            if not records:
                st.info("No players in this database.")
                return
            pid = st.selectbox(
                "Player",
                [r["id"] for r in records],
                format_func=lambda n: next(r["full_name"] for r in records if r["id"] == n),
            )
            record = next(r for r in records if r["id"] == pid)
            if action == "Update player":
                with st.form(f"update_{mode}_{pid}"):
                    values = player_form(f"edit_{mode}_{pid}", record)
                    if st.form_submit_button("Save player changes"):
                        repo.update_player(path, pid, *values)
                        st.success("Player updated. Read / search shows the saved values.")
            else:
                st.write(record)
                confirm = st.checkbox(
                    f"Confirm deletion of {record['full_name']}", key=f"confirm_{mode}_{pid}"
                )
                st.caption(
                    "Players referenced by scorecards cannot be deleted until those records are removed."
                )
                if st.button("Delete player permanently", disabled=not confirm):
                    repo.delete_player(path, pid)
                    st.success("Player deleted from the database.")
        else:
            matches = read_query(
                path, "SELECT id,description FROM matches ORDER BY match_date DESC,id DESC"
            )
            if not matches:
                st.info("No matches. Fetch provider matches and scorecards first.")
                return
            mid = st.selectbox(
                "Match",
                [m["id"] for m in matches],
                format_func=lambda n: next(m["description"] for m in matches if m["id"] == n),
            )
            innings = read_query(
                path,
                "SELECT id,number FROM innings WHERE match_id=:mid ORDER BY number",
                {"mid": mid},
            )
            if not innings:
                st.info("This match has no imported innings.")
                return
            iid = st.selectbox("Innings", [i["id"] for i in innings])
            kind = st.radio("Statistics", ["Batting", "Bowling"], horizontal=True)
            name = "batting" if kind == "Batting" else "bowling"
            rows = read_query(
                path,
                f"SELECT p.full_name,b.* FROM {name} b JOIN players p ON p.id=b.player_id WHERE innings_id=:iid",
                {"iid": iid},
            )
            table(rows, f"manage_{name}_{iid}")
            eligible = read_query(
                path,
                "SELECT p.id,p.full_name FROM players p JOIN participants a ON a.player_id=p.id JOIN innings i ON i.match_id=a.match_id WHERE i.id=:iid AND ((:bat=1 AND a.team_id=i.team_id) OR (:bat=0 AND a.team_id<>i.team_id)) ORDER BY p.full_name",
                {"iid": iid, "bat": int(kind == "Batting")},
            )
            if not eligible:
                st.info("No eligible match participants.")
                return
            pid = st.selectbox(
                "Participant",
                [p["id"] for p in eligible],
                format_func=lambda n: next(p["full_name"] for p in eligible if p["id"] == n),
            )
            existing = next((r for r in rows if r["player_id"] == pid), {})
            with st.form(f"stats_{mode}_{iid}_{kind}_{pid}"):
                runs = st.number_input(
                    "Runs scored" if kind == "Batting" else "Runs conceded",
                    min_value=0,
                    value=existing.get("runs", 0),
                    step=1,
                )
                balls = st.number_input(
                    "Balls faced" if kind == "Batting" else "Legal balls bowled",
                    min_value=0,
                    value=existing.get("balls", 0),
                    step=1,
                )
                if kind == "Batting":
                    position = st.number_input(
                        "Batting position",
                        min_value=1,
                        max_value=11,
                        value=existing.get("position", 1),
                        step=1,
                    )
                    dismissed = st.checkbox("Dismissed", value=bool(existing.get("dismissed", 0)))
                else:
                    wickets = st.number_input(
                        "Wickets",
                        min_value=0,
                        max_value=10,
                        value=existing.get("wickets", 0),
                        step=1,
                    )
                if st.form_submit_button("Create / update statistics"):
                    if kind == "Batting":
                        repo.save_batting(path, iid, pid, position, runs, balls, int(dismissed))
                    else:
                        repo.save_bowling(path, iid, pid, balls, runs, wickets)
                    st.success(
                        "Match statistics saved. Reload the table by reselecting the innings."
                    )
            confirmed = st.checkbox(
                "Confirm deletion of selected participant statistics",
                key=f"delstats_{mode}_{iid}_{pid}_{name}",
            )
            if st.button("Delete selected statistics", disabled=not confirmed):
                (repo.delete_batting if kind == "Batting" else repo.delete_bowling)(path, iid, pid)
                st.success("Statistics deleted.")
    except sqlite3.IntegrityError:
        st.error(
            "Database constraint prevented this change. Check duplicate names, occupied batting positions or referenced records."
        )
    except (ValueError, sqlite3.Error) as exc:
        st.error(str(exc))
