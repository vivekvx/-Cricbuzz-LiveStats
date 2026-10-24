"""Normalize the v1 contract. Missing facts stay missing; never infer winners."""

from datetime import datetime, timezone
from api.client import ApiError
from analytics.calculations import overs_to_balls


def cricket_format(value, international=False):
    if str(value).upper() == "T20" and international:
        return "T20I"
    return {"TEST": "Test", "ODI": "ODI", "T20I": "T20I", "T20": "T20"}.get(
        str(value).upper(), "Other"
    )


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
                            ),
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


def normalize_scorecard(payload):
    """Return validated innings; scorecard batting order follows provider batId."""
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
                        "dismissed": int(
                            str(value.get("outDesc", "")).lower()
                            not in ("", "not out", "retired hurt")
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
