"""Configuration; credentials never enter the database or logs."""

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DATA_DIR = Path(os.getenv("CRICBUZZ_DATA_DIR", str(ROOT / "data")))
API_BASE = os.getenv("CRICBUZZ_API_BASE", "https://cricbuzz-cricket.p.rapidapi.com")
API_HOST = os.getenv("CRICBUZZ_API_HOST", "cricbuzz-cricket.p.rapidapi.com")


def database_path(mode="Sample Data"):
    """Physically separate synthetic and provider records."""
    if mode not in ("Sample Data", "Live API"):
        raise ValueError("Unknown data mode")
    return DATA_DIR / ("sample.sqlite3" if mode == "Sample Data" else "live.sqlite3")


def api_key():
    """Prefer environment; optionally accept Streamlit secrets."""
    key = os.getenv("RAPIDAPI_KEY", "")
    if key:
        return key
    try:
        import streamlit as st

        return st.secrets.get("RAPIDAPI_KEY", "")
    except (FileNotFoundError, RuntimeError):
        return ""


def cloud_deployment():
    """Explicit hosting flag, configurable in environment or Cloud secrets."""
    value = os.getenv("DEPLOYMENT_ENV")
    if value is None:
        try:
            import streamlit as st

            value = st.secrets.get("DEPLOYMENT_ENV", "local")
        except (FileNotFoundError, RuntimeError):
            value = "local"
    return str(value).lower() == "community-cloud"
