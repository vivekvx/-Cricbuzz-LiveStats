"""Normalize provider contracts; missing facts stay missing and outcomes are never deduced from scores."""

from datetime import datetime, timezone
from api.client import ApiError
from analytics.calculations import overs_to_balls
from services.results import result_fields


def cricket_format(value, international=None, description=""):
    """Separate international formats from domestic and unofficial games.

    Unspecified context preserves the standalone format helper's old behavior;
    list ingestion always supplies a competition group and description.
    """
    fmt = str(value).upper()
    unofficial = any(
        term in str(description).lower() for term in ("unofficial", "warm-up", "warm up")
    )
    if unofficial or (fmt in ("TEST", "ODI") and international is False):
        return "Other"
    if fmt == "T20" and international is True:
        return "T20I"
    return {"TEST": "Test", "ODI": "ODI", "T20I": "T20I", "T20": "T20"}.get(fmt, "Other")


def normalize_matches(payload):
    if not isinstance(payload.get("typeMatches"), list):
        raise ApiError(
            "Match response lacks the v1 typeMatches list. No records imported.", "schema"
        )
    result = []
    try:
        for group in payload["typeMatches"]:
            for entry in group.get("seriesMatches", []):
                wrapper = entry.get("seriesAdWrapper")
                if not wrapper:  # Advertisement blocks are not cricket records.
                    continue
                for item in wrapper.get("matches", []):
                    info = item["matchInfo"]
                    teams = [info["team1"], info["team2"]]
                    for team in teams:
                        if not team.get("teamId") or not team.get("teamName"):
                            raise ValueError("Missing team fields")
                    state = str(info.get("state", "")).lower()
                    status = (
                        "Complete"
                        if state in ("complete", "completed", "result")
                        else "Upcoming"
                        if state in ("preview", "upcoming")
                        else "Abandoned"
                        if state in ("abandon", "abandoned")
                        else "Live"
                    )
                    winner, margin, victory_type = (
                        result_fields(info.get("status"), teams)
                        if status == "Complete"
                        else (None, None, None)
                    )
                    result.append(
                        {
                            "id": int(info["matchId"]),
                            "description": info.get("matchDesc", "Unspecified match"),
                            "teams": teams,
                            "venue": info.get("venueInfo", {}),
                            "series_id": info.get("seriesId"),
                            "series_name": info.get("seriesName"),
                            "format": cricket_format(
                                info.get("matchFormat"),
                                str(group.get("matchType", "")).lower() == "international",
                                info.get("matchDesc", ""),
                            ),
                            "provider_format": info.get("matchFormat"),
                            "competition_group": group.get("matchType", "Unknown"),
                            "winner_id": winner,
                            "margin": margin,
                            "victory_type": victory_type,
                            "date": datetime.fromtimestamp(
                                int(info["startDate"]) / 1000, timezone.utc
                            )
                            .date()
                            .isoformat(),
                            "status": status,
                            "status_text": info.get("status", ""),
                            "scores": item.get("matchScore", {}),
                            "raw": item,
                        }
                    )
    except (KeyError, TypeError, ValueError, OverflowError):
        raise ApiError(
            "Unexpected v1 match fields. No records imported; inspect provider version.", "schema"
        ) from None
    return result


def normalize_scorecard(payload, teams=None):
    """Return validated innings; scorecard batting order follows provider batId."""
    if "scorecard" in payload:
        return normalize_current_scorecard(payload, teams)
    cards = payload.get("scoreCard")
    if not isinstance(cards, list):
        raise ApiError("Scorecard unavailable or incompatible v1 scoreCard schema.", "schema")
    result = []
    try:
        for card in cards:
            bat = card["batTeamDetails"]
            bowl = card["bowlTeamDetails"]
            score = card["scoreDetails"]
            batters = []
            for index, value in enumerate(bat.get("batsmenData", {}).values(), 1):
                batters.append(
                    {
                        "id": int(value["batId"]),
                        "name": value["batName"],
                        "position": index,
                        "runs": int(value.get("runs", 0)),
                        "balls": int(value.get("balls", 0)),
                        "did_not_bat": not str(value.get("outDesc", "")).strip()
                        and int(value.get("balls", 0)) == 0
                        and int(value.get("runs", 0)) == 0,
                        "dismissed": int(
                            str(value.get("outDesc", "")).strip().lower()
                            not in ("", "not out", "batting", "retired hurt")
                        ),
                    }
                )
            bowlers = []
            for value in bowl.get("bowlersData", {}).values():
                bowlers.append(
                    {
                        "id": int(value["bowlerId"]),
                        "name": value["bowlName"],
                        "balls": overs_to_balls(value["overs"]),
                        "runs": int(value["runs"]),
                        "wickets": int(value["wickets"]),
                    }
                )
            result.append(
                {
                    "number": int(card["inningsId"]),
                    "bat_team": int(bat["batTeamId"]),
                    "bowl_team": int(bowl["bowlTeamId"]),
                    "runs": int(score["runs"]),
                    "wickets": int(score["wickets"]),
                    "balls": overs_to_balls(score["overs"]),
                    "batters": batters,
                    "bowlers": bowlers,
                }
            )
    except (KeyError, TypeError, ValueError):
        raise ApiError("Invalid v1 scorecard fields. Nothing was imported.", "schema") from None
    return result


def normalize_current_scorecard(payload, teams):
    """Parse the authenticated current lowercase scorecard response.

    Current cards identify sides by name, so resolve only against the two
    stored match teams. Do not guess missing IDs or count did-not-bat rows.
    """
    cards = payload.get("scorecard")
    if not isinstance(cards, list):
        raise ApiError("Current scorecard must contain an innings list.", "schema")
    team_lookup = {str(name).casefold(): int(tid) for name, tid in (teams or {}).items()}
    result = []
    try:
        for card in cards:
            batting_team = team_lookup[str(card["batteamname"]).casefold()]
            opposing = set(team_lookup.values()) - {batting_team}
            if len(opposing) != 1:
                raise ValueError("Cannot identify opposing match team")
            batters = []
            for position, value in enumerate(card["batsman"], 1):
                out = str(value.get("outdec", "")).strip().lower()
                balls, runs = int(value["balls"]), int(value["runs"])
                batters.append(
                    {
                        "id": int(value["id"]),
                        "name": value["name"],
                        "position": position,
                        "runs": runs,
                        "balls": balls,
                        "dismissed": int(out not in ("", "not out", "batting", "retired hurt")),
                        "did_not_bat": not out and balls == 0 and runs == 0,
                    }
                )
            bowlers = [
                {
                    "id": int(value["id"]),
                    "name": value["name"],
                    "balls": int(value["balls"])
                    if "balls" in value
                    else overs_to_balls(value["overs"]),
                    "runs": int(value["runs"]),
                    "wickets": int(value["wickets"]),
                }
                for value in card["bowler"]
            ]
            result.append(
                {
                    "number": int(card["inningsid"]),
                    "bat_team": batting_team,
                    "bowl_team": opposing.pop(),
                    "runs": int(card["score"]),
                    "wickets": int(card["wickets"]),
                    "balls": int(card["ballnbr"])
                    if "ballnbr" in card
                    else overs_to_balls(card["overs"]),
                    "batters": batters,
                    "bowlers": bowlers,
                }
            )
    except (KeyError, TypeError, ValueError):
        raise ApiError(
            "Current scorecard fields or match-team names could not be validated. Nothing imported.",
            "schema",
        ) from None
    return result
