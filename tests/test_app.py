from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
import config
import ui

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app_data(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ui, "api_key", lambda: "")
    return tmp_path


@pytest.mark.parametrize(
    "file",
    [
        "main.py",
        "pages/1_Live_Matches.py",
        "pages/2_Top_Player_Stats.py",
        "pages/3_SQL_Analytics.py",
        "pages/4_CRUD_Operations.py",
    ],
)
def test_page_smoke(app_data, file):
    at = AppTest.from_file(str(ROOT / file)).run(timeout=20)
    assert not at.exception
    assert not at.error
    assert at.sidebar.selectbox[0].value == "Sample Data"


def test_sql_execution_and_readonly_ui(app_data):
    at = AppTest.from_file(str(ROOT / "pages/3_SQL_Analytics.py")).run()
    at.button[0].click().run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 4
    at.text_area[0].set_value("DELETE FROM players").run()
    next(b for b in at.button if b.label == "Run read-only SQL").click().run()
    assert at.error
    assert not at.exception


def test_live_mode_no_fallback(app_data):
    at = AppTest.from_file(str(ROOT / "pages/1_Live_Matches.py")).run()
    at.sidebar.selectbox[0].select("Live API").run()
    assert not at.exception
    assert any("No provider snapshot" in i.value for i in at.info)
    next(b for b in at.button if b.label == "Refresh matches").click().run()
    assert any("missing" in e.value for e in at.error)
    assert len(at.dataframe) == 0


def test_create_form_validation_and_persistence(app_data):
    at = AppTest.from_file(str(ROOT / "pages/4_CRUD_Operations.py")).run()
    at.radio[0].set_value("Create player").run()
    at.text_input[0].set_value("UI Learner")
    at.text_input[1].set_value("India")
    at.button[0].click().run()
    assert not at.exception and at.success
    at.radio[0].set_value("Read / search").run()
    at.text_input[0].set_value("UI Learner").run()
    assert len(at.dataframe[0].value) == 1


def test_match_statistics_form(app_data):
    at = AppTest.from_file(str(ROOT / "pages/4_CRUD_Operations.py")).run()
    at.radio[0].set_value("Match statistics").run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 4
    assert any(b.label == "Create / update statistics" for b in at.button)
    next(r for r in at.radio if r.label == "Statistics").set_value("Bowling").run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 2


def test_hosted_demo_discloses_shared_temporary_storage(app_data, monkeypatch):
    monkeypatch.setattr(ui, "cloud_deployment", lambda: True)
    at = AppTest.from_file(str(ROOT / "main.py")).run()
    assert not at.exception
    assert any("database edits are shared" in item.value for item in at.sidebar.info)


def test_missing_cloud_key_has_working_one_click_demo(app_data):
    at = AppTest.from_file(str(ROOT / "main.py")).run()
    at.sidebar.selectbox[0].select("Live API").run()
    assert any("this deployment has no API key" in w.value for w in at.warning)
    next(b for b in at.button if b.label == "Start demo with sample data").click().run()
    assert not at.exception
    assert at.sidebar.selectbox[0].value == "Sample Data"
    assert at.metric[0].value == "60"
    assert at.metric[1].value == "8"
    assert at.metric[3].value == "25"


def test_data_source_survives_navigation_across_all_modules(app_data):
    at = AppTest.from_file(str(ROOT / "main.py")).run()
    at.sidebar.selectbox[0].select("Live API").run()
    for page in [
        "pages/1_Live_Matches.py",
        "pages/2_Top_Player_Stats.py",
        "pages/3_SQL_Analytics.py",
        "pages/4_CRUD_Operations.py",
        "main.py",
    ]:
        at.switch_page(page).run()
        assert not at.exception
        assert at.sidebar.selectbox[0].value == "Live API"
    next(b for b in at.button if b.label == "Start demo with sample data").click().run()
    at.switch_page("pages/3_SQL_Analytics.py").run()
    assert at.sidebar.selectbox[0].value == "Sample Data"


def test_player_page_chart_does_not_require_altair_import(app_data, monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "altair", None)
    at = AppTest.from_file(str(ROOT / "pages/2_Top_Player_Stats.py")).run()
    assert not at.exception
    assert len(at.get("arrow_vega_lite_chart")) == 1
    assert any(h.value == "Compare players" for h in at.subheader)


def test_live_sql_explains_q9_q16_and_explicit_sample_switch(app_data):
    from tests.test_diagnostics import one_live_card

    one_live_card(app_data / "live.sqlite3")
    at = AppTest.from_file(str(ROOT / "pages/3_SQL_Analytics.py")).run()
    at.sidebar.selectbox[0].select("Live API").run()
    next(s for s in at.selectbox if s.label == "Difficulty").select("Intermediate").run()
    next(s for s in at.selectbox if s.label == "Question").select(9).run()
    next(b for b in at.button if b.label == "Execute question").click().run()
    assert not at.exception
    assert any("highest stored runs per format: 11" in i.value for i in at.info)
    next(s for s in at.selectbox if s.label == "Question").select(16).run()
    next(b for b in at.button if b.label == "Execute question").click().run()
    assert any("single eligible year: 1" in i.value for i in at.info)
    next(b for b in at.button if b.label == "Use sample data for all 25 questions").click().run()
    assert at.sidebar.selectbox[0].value == "Sample Data"
    next(b for b in at.button if b.label == "Execute question").click().run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 24


def test_sql_all_question_check_reports_every_result(app_data):
    at = AppTest.from_file(str(ROOT / "pages/3_SQL_Analytics.py")).run()
    next(b for b in at.button if b.label == "Check all 25 questions").click().run()
    assert not at.exception
    assert any("25/25 questions have results" in i.value for i in at.info)
    assert len(at.dataframe[0].value) == 25
