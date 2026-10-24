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
    at.button[0].click().run()
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
