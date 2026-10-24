"""Parse explicit provider result text; never deduce outcomes from innings totals."""

import re


def result_fields(status, teams):
    """Recognize exact team names and standard result margins; unknowns stay NULL."""
    text = str(status or "").strip()
    for team in teams:
        name, tid = team["teamName"], int(team["teamId"])
        match = re.match(
            r"^"
            + re.escape(name)
            + r" won by (?:(an innings)(?: and (\d+) runs?)?|(\d+) (runs?|wkts?|wickets?))\b",
            text,
            re.I,
        )
        if match:
            if match[1]:
                return tid, int(match[2]) if match[2] else None, "innings"
            return tid, int(match[3]), "runs" if match[4].lower().startswith("run") else "wickets"
    return None, None, None


def explicitly_no_winner(status):
    """Recognize an explicit non-decisive correction, not missing result text."""
    text = str(status or "").strip().lower()
    if "won" in text:
        return False
    return bool(
        re.match(
            r"^(?:match (?:drawn|tied|abandoned|cancelled|canceled)|no result|abandoned|cancelled|canceled)\b",
            text,
        )
    )
