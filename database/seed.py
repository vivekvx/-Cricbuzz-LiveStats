"""Deterministic fictional data. No real player performance is asserted."""

from datetime import date, timedelta
from database.connection import connect, initialize

DEMO_DATE = "2026-10-24"


def seed(path):
    """Seed once, transactionally; do not resurrect user-deleted records."""
    initialize(path)
    with connect(path) as c:
        # Serialize the seed-marker check and inserts across first-time visitors.
        c.execute("BEGIN IMMEDIATE")
        if c.execute("SELECT 1 FROM metadata WHERE key='seed_version'").fetchone():
            return
        c.executemany(
            "INSERT INTO teams VALUES(?,?,?,?)",
            [
                (1, "India Demo XI", "India", "synthetic-v1"),
                (2, "Australia Demo XI", "Australia", "synthetic-v1"),
            ],
        )
        names = [
            "Aarav Demo",
            "Bhavna Demo",
            "Chirag Demo",
            "Diya Demo",
            "Evan Demo",
            "Freya Demo",
            "Glen Demo",
            "Hana Demo",
        ]
        for idx, name in enumerate(names, 1):
            role = ["All-rounder", "Batsman", "Bowler", "Wicket-keeper"][(idx - 1) % 4]
            c.execute(
                "INSERT INTO players VALUES(?,?,?,?,?,?,?,?)",
                (
                    idx,
                    name,
                    "India" if idx <= 4 else "Australia",
                    role,
                    "Right-hand bat",
                    "Right-arm medium",
                    "synthetic-v1",
                    None,
                ),
            )
        c.executemany(
            "INSERT INTO venues VALUES(?,?,?,?,?,?)",
            [
                (1, "Demo Oval", "Demo Delhi", "India", 60000, "synthetic-v1"),
                (2, "Demo Park", "Demo Sydney", "Australia", 50000, "synthetic-v1"),
                (3, "Demo Neutral", "Demo City", "UAE", None, "synthetic-v1"),
            ],
        )
        c.execute(
            "INSERT INTO series VALUES(1,?,?,?,?,?,?)",
            ("Synthetic Analytics Series", "India", "ODI", "2024-01-01", 60, "synthetic-v1"),
        )
        dates = [
            date(2024 + q // 4, (q % 4) * 3 + 1, 5 + k * 3) for q in range(9) for k in range(6)
        ]
        dates += [date.fromisoformat(DEMO_DATE) - timedelta(days=6 - k) for k in range(6)]
        for n, day in enumerate(dates):
            mid = n + 1
            fmt = ["Test", "ODI", "T20I"][n % 3]
            winner = 1 if n % 3 else 2
            margin, method = (20, "runs") if n % 2 else (4, "wickets")
            first = winner if method == "runs" else 3 - winner
            toss = 1 if n % 2 else 2
            decision = "bat" if toss == first else "bowl"
            c.execute(
                "INSERT INTO matches VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    mid,
                    f"Synthetic fixture {mid}",
                    1,
                    2,
                    1 + n % 3,
                    1,
                    day.isoformat(),
                    fmt,
                    "Complete",
                    "Synthetic completed fixture",
                    winner,
                    margin,
                    method,
                    toss,
                    decision,
                    first,
                    "synthetic-v1",
                ),
            )
            for pid in range(1, 9):
                team = 1 if pid <= 4 else 2
                c.execute("INSERT INTO participants VALUES(?,?,?)", (mid, pid, team))
                c.execute("INSERT INTO fielding VALUES(?,?,?,?)", (mid, pid, 1, int(pid % 4 == 0)))
            for ino, team in enumerate((first, 3 - first), 1):
                iid = mid * 10 + ino
                start = 1 if team == 1 else 5
                scores = [40 + n * 2 + j * 4 for j in range(4)]
                c.execute(
                    "INSERT INTO innings VALUES(?,?,?,?,?,?,?)",
                    (iid, mid, ino, team, sum(scores), 4, 120 if fmt == "T20I" else 300),
                )
                for j, pid in enumerate(range(start, start + 4)):
                    c.execute(
                        "INSERT INTO batting VALUES(?,?,?,?,?,?)",
                        (iid, pid, j + 1, scores[j], 30 + j * 4, int(j != 3)),
                    )
                for pid in [1, 3] if team == 2 else [5, 7]:
                    c.execute(
                        "INSERT INTO bowling VALUES(?,?,?,?,?)", (iid, pid, 24, 24 + n % 7, 3)
                    )
        c.execute("INSERT INTO metadata VALUES('seed_version','synthetic-v1')")
        c.execute("INSERT INTO metadata VALUES('as_of',?)", (DEMO_DATE,))


if __name__ == "__main__":
    from config import database_path

    seed(database_path())
    print("Synthetic demonstration database initialized.")
