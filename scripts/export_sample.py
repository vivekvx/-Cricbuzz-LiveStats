"""Export deterministic synthetic rows in dependency order for SQL-only setup."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database.connection import connect  # noqa: E402
from database.seed import seed  # noqa: E402


def export():
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "sample.sqlite3"
        seed(path)
        statements = ["-- SYNTHETIC-V1 ONLY. No real player performances.", "BEGIN;"]
        with connect(path) as c:
            for table in [
                "teams",
                "players",
                "venues",
                "series",
                "matches",
                "participants",
                "innings",
                "batting",
                "bowling",
                "fielding",
                "metadata",
            ]:
                cols = [r["name"] for r in c.execute(f"PRAGMA table_info({table})")]
                quoted = ",".join(f'quote("{col}")' for col in cols)
                for row in c.execute(f"SELECT {quoted} FROM {table}"):
                    statements.append(f"INSERT OR IGNORE INTO {table} VALUES({','.join(row)});")
        statements.append("COMMIT;")
        (ROOT / "data/sample_data/seed.sql").write_text("\n".join(statements) + "\n")


if __name__ == "__main__":
    export()
