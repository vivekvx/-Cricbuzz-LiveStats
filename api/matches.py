"""Cricbuzz Cricket v1 endpoint adapter (not the incompatible v2 API)."""

from api.client import identifier


def match_list(client, category="live"):
    if category not in ("live", "recent", "upcoming"):
        raise ValueError("Invalid match category")
    return client.get(f"/matches/v1/{category}")


def scorecard(client, match_id):
    return client.get(f"/mcenter/v1/{identifier(match_id)}/scard")


def series_matches(client, series_id):
    return client.get(f"/series/v1/{identifier(series_id)}")


def venue_details(client, venue_id):
    return client.get(f"/venues/v1/{identifier(venue_id)}")
