"""Provider timestamps, distinct from the time our application fetched a payload."""

from datetime import datetime, timezone


def provider_timestamp(payload):
    value = payload.get("responseLastUpdated", payload.get("responselastupdated"))
    try:
        seconds = float(value)
        if seconds > 100000000000:
            seconds /= 1000
        if seconds <= 0:
            return None
        return datetime.fromtimestamp(seconds, timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None
