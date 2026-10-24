"""Record actual browser interactions against the running local Streamlit app."""

import os
import sys
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import database_path  # noqa: E402
from database.repository import players  # noqa: E402

BASE = os.getenv("DEMO_URL", "http://127.0.0.1:8501")
OUT = ROOT / "docs/demo_frames"
OUT.mkdir(exist_ok=True)
NAME = "Walkthrough Learner"


def run():
    """Exercise real forms, persist a CRUD lifecycle, and save browser video."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.getenv(
                "CHROME_EXECUTABLE", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ),
            headless=True,
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            record_video_dir=str(OUT),
            record_video_size={"width": 1440, "height": 1000},
        )
        page = context.new_page()
        page.set_default_timeout(20000)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        def pause(name):
            page.wait_for_timeout(1800)
            assert page.get_by_test_id("stException").count() == 0
            page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
            print(name, flush=True)

        def goto(route, title):
            page.goto(BASE + route)
            page.get_by_role("heading", name=title, exact=True).wait_for()
            page.wait_for_timeout(700)

        def choose(label, option, regex=False):
            box = (
                page.get_by_test_id("stSelectbox")
                .filter(has=page.get_by_text(label, exact=True))
                .get_by_role("combobox")
            )
            box.click()
            page.get_by_role(
                "option", name=re.compile(option) if regex else option, exact=not regex
            ).click()
            page.wait_for_timeout(600)

        goto("", "Cricbuzz LiveStats")
        pause("01_home")
        goto("/Live_Matches", "Match centre")
        pause("02_match_centre")
        page.get_by_role("heading", name=re.compile("Innings 1")).scroll_into_view_if_needed()
        pause("03_scorecard")
        goto("/Top_Player_Stats", "Player statistics")
        choose("Cricket format", "ODI")
        pause("04_player_stats")
        goto("/SQL_Analytics", "SQL queries & analytics")
        page.get_by_role("button", name="Execute question", exact=True).click()
        pause("05_beginner_sql")
        choose("Difficulty", "Intermediate")
        choose("Question", "^Q13", regex=True)
        page.get_by_role("button", name="Execute question", exact=True).click()
        page.get_by_test_id("stDataFrame").first.scroll_into_view_if_needed()
        pause("06_intermediate_sql")
        choose("Difficulty", "Advanced")
        choose("Question", "^Q21", regex=True)
        page.get_by_role("button", name="Execute question", exact=True).click()
        page.get_by_test_id("stDataFrame").first.scroll_into_view_if_needed()
        pause("07_advanced_sql")
        page.get_by_role("textbox", name="SQL", exact=True).fill("DELETE FROM players;")
        page.get_by_role("button", name="Run read-only SQL", exact=True).click()
        page.get_by_test_id("stAlert").filter(has_text="rejected").wait_for()
        pause("08_readonly_rejection")
        goto("/CRUD_Operations", "Manage records")
        page.get_by_text("Create player", exact=True).first.click()
        page.get_by_role("textbox", name="Full name", exact=True).fill(NAME)
        page.get_by_role("textbox", name="Country represented", exact=True).fill("India")
        page.get_by_role("button", name="Create player", exact=True).click()
        page.get_by_test_id("stAlert").filter(has_text="created and saved").wait_for()
        assert len(players(database_path(), NAME)) == 1
        pause("09_create_player")
        page.get_by_text("Update player", exact=True).first.click()
        choose("Player", NAME)
        page.get_by_role("textbox", name="Country represented", exact=True).fill("Australia")
        page.get_by_role("button", name="Save player changes", exact=True).click()
        page.get_by_test_id("stAlert").filter(has_text="updated").wait_for()
        assert players(database_path(), NAME)[0]["country"] == "Australia"
        pause("10_update_player")
        page.get_by_text("Read / search", exact=True).click()
        page.get_by_role("textbox", name="Search players", exact=True).fill(NAME)
        page.get_by_role("textbox", name="Search players", exact=True).press("Enter")
        expect(page.get_by_test_id("stDataFrame")).to_be_visible()
        pause("11_read_updated_player")
        page.get_by_text("Delete player", exact=True).first.click()
        choose("Player", NAME)
        page.get_by_text(f"Confirm deletion of {NAME}", exact=True).click()
        page.get_by_role("button", name="Delete player permanently", exact=True).click()
        page.get_by_test_id("stAlert").filter(has_text="deleted from the database").wait_for()
        assert players(database_path(), NAME) == []
        pause("12_delete_player")
        page.get_by_text("Read / search", exact=True).click()
        page.get_by_role("textbox", name="Search players", exact=True).fill(NAME)
        page.get_by_role("textbox", name="Search players", exact=True).press("Enter")
        page.get_by_test_id("stAlert").filter(has_text="No records").wait_for()
        pause("13_verify_deleted")
        assert not errors, errors
        video = page.video
        context.close()
        video_path = video.path()
        browser.close()
        print(f"VIDEO={video_path}", flush=True)
        (ROOT / "docs/demo_recording.json").write_text(
            __import__("json").dumps(
                {
                    "browser_errors": errors,
                    "stages": 13,
                    "crud_verified_in_database": True,
                    "source": "synthetic-v1",
                    "video": Path(video_path).name,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    run()
