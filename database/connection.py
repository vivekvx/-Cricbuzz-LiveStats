"""Connection factory and bounded, authorized read-only SQL execution."""

import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Stddev:
    """Population standard deviation using Welford's stable algorithm."""

    def __init__(self):
        self.n, self.mean, self.m2 = 0, 0.0, 0.0

    def step(self, value):
        if value is not None:
            self.n += 1
            delta = value - self.mean
            self.mean += delta / self.n
            self.m2 += delta * (value - self.mean)

    def finalize(self):
        return math.sqrt(max(0, self.m2 / self.n)) if self.n else None


@contextmanager
def connect(path):
    """Enable FK checks, commit atomically, and close connections."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.create_aggregate("stddev_pop", 1, Stddev)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize(path):
    """Idempotently apply version-one schema."""
    with connect(path) as conn:
        conn.executescript(Path(__file__).with_name("schema.sql").read_text())
        conn.execute("INSERT OR IGNORE INTO metadata VALUES('schema_version','1')")
        from database.migrations import apply

        apply(conn)


def read_query(path, sql, params=None, limit=5000):
    """SQLite authorizer is the security boundary, not keyword matching."""
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_aggregate("stddev_pop", 1, Stddev)
    allowed = {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
        sqlite3.SQLITE_RECURSIVE,
    }

    def authorize(action, arg1, arg2, db, trigger):
        if action not in allowed:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and str(arg2).lower() in (
            "load_extension",
            "writefile",
            "readfile",
        ):
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    conn.set_authorizer(authorize)
    budget = [0]

    def progress():
        budget[0] += 1
        return int(budget[0] > 10000)

    conn.set_progress_handler(progress, 1000)
    try:
        cursor = conn.execute(sql, params or {})
        if cursor.description is None:
            raise ValueError("Only queries returning rows are allowed")
        rows = cursor.fetchmany(limit + 1)
        if len(rows) > limit:
            raise ValueError(f"Result exceeds {limit} rows. Add LIMIT or narrow the query.")
        return [dict(r) for r in rows]
    finally:
        conn.close()
