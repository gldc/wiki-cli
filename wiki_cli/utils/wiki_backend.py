"""Wiki.js GraphQL backend client.

This module handles all communication with a running Wiki.js instance
via its GraphQL API. Wiki.js is the hard dependency — without a running
instance, this CLI is useless.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

import requests


# ── Configuration ────────────────────────────────────────────────────

DEFAULT_CONFIG_DIR = Path.home() / ".wiki-cli"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"


def load_config(config_path: Optional[str] = None) -> dict:
    """Load Wiki.js connection configuration.

    Config is stored at ~/.wiki-cli/config.json with fields:
      - url: Wiki.js base URL (e.g., http://localhost:3000)
      - api_key: API key for authentication

    Environment variables override file config:
      - WIKI_URL
      - WIKI_API_KEY
    """
    config = {"url": "", "api_key": ""}

    path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
    if path.exists():
        with open(path) as f:
            config.update(json.load(f))

    # Environment overrides
    if os.environ.get("WIKI_URL"):
        config["url"] = os.environ["WIKI_URL"]
    if os.environ.get("WIKI_API_KEY"):
        config["api_key"] = os.environ["WIKI_API_KEY"]

    return config


def save_config(url: str, api_key: str, config_path: Optional[str] = None):
    """Save Wiki.js connection configuration."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"url": url, "api_key": api_key}, f, indent=2)


def validate_config(config: dict):
    """Validate that config has required fields. Raises RuntimeError if not."""
    if not config.get("url"):
        raise RuntimeError(
            "Wiki.js URL not configured. Set it with:\n"
            "  wiki-cli connect <url> --api-key <key>\n"
            "Or set environment variables:\n"
            "  export WIKI_URL=http://localhost:3000\n"
            "  export WIKI_API_KEY=your-api-key\n\n"
            "Wiki.js must be running and API access enabled.\n"
            "Enable API access: Administration → API Access → Enable API"
        )
    if not config.get("api_key"):
        raise RuntimeError(
            "Wiki.js API key not configured. Set it with:\n"
            "  wiki-cli connect <url> --api-key <key>\n"
            "Or: export WIKI_API_KEY=your-api-key\n\n"
            "Create an API key: Administration → API Access → Create API Key"
        )


# ── GraphQL Client ───────────────────────────────────────────────────


class WikiClient:
    """GraphQL client for Wiki.js API."""

    def __init__(self, url: str, api_key: str, timeout: int = 30):
        self.url = url.rstrip("/")
        self.graphql_url = f"{self.url}/graphql"
        self.api_key = api_key
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )

    def execute(self, query: str, variables: Optional[dict] = None) -> dict:
        """Execute a GraphQL query/mutation.

        Returns the response data dict. Raises RuntimeError on errors.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            resp = self._session.post(
                self.graphql_url,
                json=payload,
                timeout=self.timeout,
            )
        except requests.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Wiki.js at {self.url}\n"
                "Ensure Wiki.js is running and accessible."
            )
        except requests.Timeout:
            raise RuntimeError(f"Request to Wiki.js timed out after {self.timeout}s")

        if resp.status_code == 401:
            raise RuntimeError(
                "Authentication failed. Check your API key.\n"
                "Create a new key: Administration → API Access"
            )
        if resp.status_code == 403:
            raise RuntimeError(
                "Permission denied. Your API key may lack required permissions."
            )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Wiki.js returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

        result = resp.json()
        if "errors" in result:
            errors = result["errors"]
            msgs = [e.get("message", str(e)) for e in errors]
            raise RuntimeError(f"GraphQL error: {'; '.join(msgs)}")

        return result.get("data", {})

    def test_connection(self) -> dict:
        """Test connection to Wiki.js. Returns system info on success."""
        query = """
        {
            system {
                info {
                    currentVersion
                    hostname
                    operatingSystem
                    platform
                    dbType
                    nodeVersion
                    cpuCores
                    ramTotal
                    workingDirectory
                    pagesTotal
                    usersTotal
                    groupsTotal
                    tagsTotal
                }
            }
        }
        """
        data = self.execute(query)
        return data.get("system", {}).get("info", {})


def create_client(config: Optional[dict] = None) -> WikiClient:
    """Create a WikiClient from config (file + env vars).

    Validates configuration and returns a ready-to-use client.
    """
    if config is None:
        config = load_config()
    validate_config(config)
    return WikiClient(url=config["url"], api_key=config["api_key"])
