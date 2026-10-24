"""Shared input validation."""

ROLES = ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"]


def player_fields(name, country, role, batting_style, bowling_style):
    values = [str(v).strip() for v in (name, country, role, batting_style, bowling_style)]
    if any(not v or len(v) > 120 for v in values):
        raise ValueError("All player fields are required and must contain 1–120 characters.")
    if role not in ROLES:
        raise ValueError("Select a valid playing role.")
    return values
