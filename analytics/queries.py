"""Execute a registered query with an explicit date reference."""

from analytics.query_registry import QUESTIONS
from database.connection import read_query


def execute(path, number, as_of):
    if not 1 <= number <= 25:
        raise ValueError("Question must be between 1 and 25")
    return read_query(path, QUESTIONS[number - 1]["sql"], {"as_of": as_of})
