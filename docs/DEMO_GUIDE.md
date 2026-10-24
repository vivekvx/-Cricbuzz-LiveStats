# Demonstration script

Use Sample Data throughout this credential-free demo. Say explicitly that every player and score is synthetic. Do not describe any synthetic card as a live match. The separate Live API module requires a subscribed compatible key; never display the key during recording.

1. Start `streamlit run main.py` from the activated project environment. Open localhost:8501.
2. **Home:** explain the REST → Python → SQLite → Streamlit flow, inspect initialization status and counts. Point out the source selector and fixed demo reference date.
3. **Match centre:** open a synthetic fixture. Show its teams, date, format, venue, status, innings totals, batting card and bowling card. Explain manual refresh in provider mode and the stored-snapshot timestamp.
4. **Player statistics:** select ODI. Explore runs, highest score, wickets, batting average and economy leaderboards. Compare two players. Explain that not-out-only averages are undefined and that career scope is the stored dataset. Export a CSV.
5. **Beginner analytics:** run Q1 and Q3. Read the exact question, inspect SQL, and compare the ODI totals with Player statistics.
6. **Intermediate analytics:** run Q13 and Q14. Explain the adjacent-batting-position proxy, then the 24-ball/three-appearance eligibility rule.
7. **Advanced analytics:** run Q21, Q23 and Q25. Explain weighted ranking, published form thresholds and quarterly career phases. Expand assumptions and export results.
8. **Custom SQL:** run `SELECT full_name,role FROM players;`. Attempt `DELETE FROM players;` to demonstrate rejection and unchanged data.
9. **Create:** Manage records → Create player. Enter `Demo Learner`, country `India`, role `Batsman`, batting `Right-hand bat`, bowling `None`. Submit and show success.
10. **Read:** search for `Demo Learner`, showing the persisted row.
11. **Update:** select that player, change country to `Australia`, submit. Search again and verify the saved value.
12. **Delete:** select the same player, check the confirmation and delete. Search again; zero rows proves persistence. Existing referenced sample players remain protected by foreign keys.
13. **Match statistics:** select a match and innings, inspect records, update a batter's runs, reselect to read the saved value, and restore it. The automated tests separately cover create/delete and opposing-team validation.
14. **Live access state:** optionally choose Live API with no key and press Refresh matches; show the actionable credentials error and the absence of sample fallback. Return to Sample Data.

## Reproduce the recording

The supplied `docs/demo.mp4` records real browser interactions: Home, Match centre, Player statistics, three query difficulties, read-only SQL rejection, and the complete player CRUD lifecycle. It is silent; use the script above for narration.

Optional recording dependencies are in requirements-dev.txt. Install the Playwright media helper once:

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install ffmpeg
# App should already be running on port 8501.
python scripts/record_demo.py
```

The recorder uses an installed Google Chrome (macOS default path; set CHROME_EXECUTABLE for another path). It writes a browser WebM plus labeled screenshots under docs/demo_frames. Convert the returned WebM with FFmpeg to MP4. The recorder never enters Live API mode or accesses secrets. It verifies the created/updated/deleted record through the UI and database. Generated recordings may be regenerated without changing source.
