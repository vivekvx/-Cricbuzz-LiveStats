"""Disclose missing live evidence instead of presenting unknowns as complete stats."""

from database.connection import read_query


def live_warnings(path, question):
    rows = read_query(
        path,
        """SELECT
      (SELECT COUNT(*) FROM matches WHERE status='Complete') completed,
      (SELECT COUNT(*) FROM matches WHERE status='Complete' AND winner_id IS NULL
       AND lower(COALESCE(status_text,'')) NOT LIKE '%draw%'
       AND lower(COALESCE(status_text,'')) NOT LIKE '%tie%'
       AND lower(COALESCE(status_text,'')) NOT LIKE '%no result%'
       AND lower(COALESCE(status_text,'')) NOT LIKE '%abandon%') missing_results,
      (SELECT COUNT(*) FROM matches WHERE toss_winner_id IS NOT NULL) tosses,
      (SELECT COUNT(*) FROM fielding) fielding_rows,
      (SELECT COUNT(*) FROM series) series_rows,
      (SELECT COUNT(*) FROM venues WHERE capacity IS NOT NULL) capacities,
      (SELECT COUNT(*) FROM teams WHERE country<>'Unknown') team_countries,
      (SELECT COUNT(*) FROM venues WHERE country<>'Unknown') venue_countries""",
    )[0]
    messages = [
        "Live analytics cover imported snapshots only, not a complete cricket history. Career totals below describe stored scorecards; API career tables are displayed separately on Player statistics."
    ]
    if question in (5, 10, 12, 15, 17, 22) and rows["missing_results"]:
        messages.append(
            f"{rows['missing_results']} of {rows['completed']} completed matches lack a recognized outcome. Win totals and close-match analysis are incomplete; unknown outcomes are not losses."
        )
    if question == 17 and not rows["tosses"]:
        messages.append(
            "Toss data has not been imported. An empty result does not mean winning the toss has no effect."
        )
    if question == 21 and not rows["fielding_rows"]:
        messages.append(
            "Fielding records are unavailable. The documented formula assigns zero to missing fielding components, so this is a partial ranking, not a complete overall ranking."
        )
    if question == 8 and not rows["series_rows"]:
        messages.append(
            "Series metadata has not been imported; this database cannot establish whether any series started in 2024."
        )
    if question == 4 and not rows["capacities"]:
        messages.append(
            "Venue capacities have not been imported; an empty result does not mean no large venues exist."
        )
    if question == 12 and (not rows["team_countries"] or not rows["venue_countries"]):
        messages.append(
            "Home/away analysis lacks represented-country or venue-country metadata. Unknown countries are excluded."
        )
    return messages
