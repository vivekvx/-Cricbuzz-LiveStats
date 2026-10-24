"""Assignment-compatible centralized connection entry point."""

from database.connection import connect, initialize, read_query

__all__ = ["connect", "initialize", "read_query"]
