from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st

from utils.matches import FOOTBALL_DATA_BASE, _api_headers
from utils.teams import resolve_team_name
from config.logging import logger

STANDINGS_COLUMNS = ["#", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]
TEAMS_PER_GROUP = 4
STANDINGS_TABLE_HEIGHT = 38 + TEAMS_PER_GROUP * 35


def _stat(value: Any, default: int = 0) -> int:
    return default if value is None else int(value)


def _parse_group_key(group_label: str) -> str:
    return group_label.replace("Group ", "").strip() or group_label


def _parse_entry(entry: dict[str, Any]) -> dict[str, Any]:
    team = entry.get("team") or {}

    return {
        "#": _stat(entry.get("position")),
        "Team": resolve_team_name(team.get("name", "")),
        "P": _stat(entry.get("playedGames")),
        "W": _stat(entry.get("won")),
        "D": _stat(entry.get("draw")),
        "L": _stat(entry.get("lost")),
        "GF": _stat(entry.get("goalsFor")),
        "GA": _stat(entry.get("goalsAgainst")),
        "GD": _stat(entry.get("goalDifference")),
        "Pts": _stat(entry.get("points")),
    }


def _parse_api_response(response: dict[str, Any]) -> dict[str, pd.DataFrame]:
    if not response:
        return {}

    group_tables = response.get("standings") or []
    standings: dict[str, pd.DataFrame] = {}

    for group_table in group_tables:
        if not group_table:
            continue

        table = group_table.get("table") or []
        rows = [_parse_entry(entry) for entry in table[:TEAMS_PER_GROUP]]
        if not rows:
            continue

        group_label = str(group_table.get("group", ""))
        group_key = _parse_group_key(group_label)
        standings[group_key] = pd.DataFrame(rows)[STANDINGS_COLUMNS]

    return dict(sorted(standings.items(), key=lambda item: item[0]))


def _fetch_standings_response(api_key: str) -> dict[str, Any]:
    response = requests.get(
        f"{FOOTBALL_DATA_BASE}competitions/WC/standings",
        headers=_api_headers(FOOTBALL_DATA_BASE, api_key),
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        logger.error(f"API error: {payload['errors']}")
        raise RuntimeError(str(payload["errors"]))
    return payload


def get_football_data_key() -> str | None:
    return os.getenv("FOOTBALL_DATA_KEY") or st.secrets.get("FOOTBALL_DATA_KEY") or None


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_group_standings(api_key: str) -> dict[str, pd.DataFrame]:
    logger.info("Fetching group standings...")
    response = _fetch_standings_response(api_key)
    logger.info("Fetched successfully")
    return _parse_api_response(response)


def get_group_standings(api_key: str | None = None) -> dict[str, pd.DataFrame]:
    key = api_key or get_football_data_key()
    if not key:
        return {}
    return fetch_group_standings(key)
