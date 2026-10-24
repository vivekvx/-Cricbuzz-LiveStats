"""Small, synchronous RapidAPI client with bounded retries and sanitized errors."""

import re
import time
from urllib.parse import urlparse
import requests
from config import API_BASE, API_HOST, api_key


class ApiError(RuntimeError):
    """A safe error message suitable for display in the dashboard."""

    def __init__(self, message, kind="provider"):
        super().__init__(message)
        self.kind = kind


class Client:
    def __init__(self, key=None, base_url=API_BASE, host=API_HOST, session=None, sleep=time.sleep):
        self.key = api_key() if key is None else key
        parsed = urlparse(base_url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.query:
            raise ValueError("API base must be a valid HTTPS URL without credentials or query.")
        self.base = base_url.rstrip("/")
        self.host = host
        self.session = session or requests.Session()
        self.sleep = sleep

    def get(self, path, params=None):
        """GET JSON; retry transient errors only, at most three attempts."""
        if not self.key:
            raise ApiError(
                "RAPIDAPI_KEY is missing. Configure a subscribed key or select Sample Data.",
                "credentials",
            )
        if not re.fullmatch(r"/[A-Za-z0-9/_-]+", path):
            raise ValueError("Invalid API path")
        for attempt in range(3):
            try:
                response = self.session.get(
                    self.base + path,
                    params=params,
                    headers={"X-RapidAPI-Key": self.key, "X-RapidAPI-Host": self.host},
                    timeout=(5, 20),
                    allow_redirects=False,
                )
            except requests.RequestException:
                if attempt == 2:
                    raise ApiError(
                        "Connection failed after three attempts; try again later.", "network"
                    ) from None
                self.sleep(2**attempt)
                continue
            if response.status_code in (401, 403):
                raise ApiError(
                    "API authorization failed. Check the key, subscription and selected API version.",
                    "credentials",
                )
            if response.status_code == 404:
                raise ApiError(
                    "Provider endpoint or resource unavailable (404). Check the documented API version.",
                    "not_found",
                )
            if response.status_code == 429:
                # Do not spend additional quota automatically on a rate-limited response.
                retry = response.headers.get("Retry-After", "not supplied")
                if not re.fullmatch(r"[0-9]{1,6}", retry):
                    retry = "not supplied"
                raise ApiError(
                    f"Rate limit reached. Retry-After seconds: {retry}. Refresh later.",
                    "rate_limit",
                )
            if 500 <= response.status_code < 600 and attempt < 2:
                self.sleep(2**attempt)
                continue
            if not 200 <= response.status_code < 300:
                raise ApiError(f"Provider request failed (HTTP {response.status_code}).")
            try:
                payload = response.json()
            except ValueError:
                raise ApiError("Provider returned invalid JSON.", "schema") from None
            if not isinstance(payload, dict):
                raise ApiError("Expected a JSON object from the configured v1 provider.", "schema")
            return payload
        raise ApiError("Provider unavailable after bounded retries.")


def identifier(value):
    """Reject invalid identifiers before building paths."""
    if isinstance(value, bool) or not str(value).isdigit() or int(value) <= 0:
        raise ValueError("A positive numeric provider ID is required.")
    return int(value)
