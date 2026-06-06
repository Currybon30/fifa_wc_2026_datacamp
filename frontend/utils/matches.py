"""Match data helpers: API-Sports live fixtures with local CSV fallback."""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from config.logging import logger

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

from utils.teams import resolve_team_name

load_dotenv()

API_FOOTBALL_BASE = os.getenv("API_FOOTBALL_HOST") or st.secrets.get("API_FOOTBALL_HOST")
FOOTBALL_DATA_BASE = os.getenv("FOOTBALL_DATA_HOST") or st.secrets.get("FOOTBALL_DATA_HOST")
WORLD_CUP_LEAGUE_ID = 1
WORLD_CUP_SEASON = 2022 # Change to 2026 when the season starts
MATCH_DURATION_MINUTES = 105

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")
GROUP_FIXTURES_CSV = (
    PROJECT_ROOT
    / "FIFA World Cup 2026 - DataCamp Competition"
    / "data"
    / "group_fixtures.csv"
)

KNOCKOUT_SLOTS_CSV = (
    PROJECT_ROOT
    / "FIFA World Cup 2026 - DataCamp Competition"
    / "data"
    / "knockout_slots.csv"
)

_FIXTURE_COLUMNS = [
    "match_id",
    "stage",
    "group",
    "round",
    "home_team",
    "away_team",
    "date_utc",
    "venue",
]

LIVE_STATUSES = {"1H", "HT", "2H", "ET", "BT", "P", "LIVE", "INT"}
FINISHED_STATUSES = {"FT", "AET", "PEN", "AWD", "WO"}


@st.cache_data(ttl=60, show_spinner=False)
def load_group_fixtures() -> pd.DataFrame:
    df = pd.read_csv(GROUP_FIXTURES_CSV)
    df["date_utc"] = pd.to_datetime(df["date_utc"], utc=True)
    df["home_team"] = df["home_team"].map(resolve_team_name)
    df["away_team"] = df["away_team"].map(resolve_team_name)
    df["stage"] = "group"
    df["round"] = "Group " + df["group"].astype(str)
    return df[_FIXTURE_COLUMNS].sort_values("date_utc").reset_index(drop=True)


@st.cache_data(ttl=60, show_spinner=False)
def load_knockout_slots() -> pd.DataFrame:
    df = pd.read_csv(KNOCKOUT_SLOTS_CSV)
    df["date_utc"] = pd.to_datetime(df["date_utc"], utc=True)
    df = df.rename(columns={"slot_home": "home_team", "slot_away": "away_team"})
    df["stage"] = "knockout"
    df["group"] = pd.NA
    return df[_FIXTURE_COLUMNS].sort_values("date_utc").reset_index(drop=True)


@st.cache_data(ttl=60, show_spinner=False)
def load_local_fixtures() -> pd.DataFrame:
    combined = pd.concat([load_group_fixtures(), load_knockout_slots()], ignore_index=True)
    return combined.sort_values("date_utc").reset_index(drop=True)


def get_football_data_key() -> str | None:
    return os.getenv("FOOTBALL_DATA_KEY") or st.secrets.get("FOOTBALL_DATA_KEY") or None

def get_api_football_key() -> str | None:
    return os.getenv("API_FOOTBALL_KEY") or st.secrets.get("API_FOOTBALL_KEY") or None


def _api_headers(base: str, api_key: str) -> dict[str, str]:
    if base == FOOTBALL_DATA_BASE:
        return {"X-Auth-Token": api_key}
    elif base == API_FOOTBALL_BASE:
        return {"x-apisports-key": api_key}
    else:
        raise ValueError(f"Invalid base: {base}")


def _api_get(base: str, path: str, api_key: str, params: dict[str, Any] | None = None):
    response = requests.get(
        f"{base}{path}",
        headers=_api_headers(base, api_key),
        params=params or {},
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        logger.error(f"API error: {payload['errors']}")
        raise RuntimeError(str(payload["errors"]))
    if base == FOOTBALL_DATA_BASE:
        return payload
    elif base == API_FOOTBALL_BASE:
        return payload.get("response")
    else:
        raise ValueError(f"Invalid base: {base}")


@st.cache_data(ttl=1200, show_spinner=False)
def fetch_api_fixtures(api_key: str) -> dict: # Use this for final scores
    logger.info(f"Fetching API fixtures...")
    fixtures = _api_get(
        FOOTBALL_DATA_BASE,
        "competitions/WC/matches",
        api_key
    )
    logger.info(f"Fetched successfully")
    return fixtures

@st.cache_data(ttl=1200, show_spinner=False)
def fetch_live_fixtures(api_key: str) -> list[dict]:
    logger.info(f"Fetching live fixtures...")
    fixtures = _api_get(API_FOOTBALL_BASE, "/fixtures", api_key, {"live": "all"})
    logger.info(f"Fetched successfully")
    # return [f for f in fixtures if f.get("league", {}).get("id") == WORLD_CUP_LEAGUE_ID]
    return fixtures


def _local_status(row: pd.Series, now: datetime) -> str:
    kickoff = row["date_utc"].to_pydatetime()
    if kickoff > now:
        return "NS"
    if kickoff <= now <= kickoff + pd.Timedelta(minutes=MATCH_DURATION_MINUTES):
        return "LIVE"
    return "FT"


def split_local_fixtures(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    now = datetime.now(timezone.utc)
    statuses = df.apply(lambda row: _local_status(row, now), axis=1)
    live = df[statuses == "LIVE"].copy()
    upcoming = df[statuses == "NS"].copy()
    completed = df[statuses == "FT"].copy()
    return live, upcoming, completed


def filter_upcoming_local_fixtures(
    upcoming_df: pd.DataFrame,
    *,
    live_df: pd.DataFrame | None = None,
    live_fixtures: list[dict] | None = None,
    completed_df: pd.DataFrame | None = None,
    completed_fixtures: list[dict] | None = None,
) -> pd.DataFrame:
    if upcoming_df.empty:
        return upcoming_df

    excluded_pairs: set[tuple[str, str]] = set()

    for source_df in (live_df, completed_df):
        if source_df is not None and len(source_df):
            for _, row in source_df.iterrows():
                excluded_pairs.add((row["home_team"], row["away_team"]))

    if live_fixtures:
        for fixture in live_fixtures:
            excluded_pairs.add((fixture_home_team(fixture), fixture_away_team(fixture)))

    if completed_fixtures:
        for match in completed_fixtures:
            excluded_pairs.add((fd_match_home_team(match), fd_match_away_team(match)))

    if not excluded_pairs:
        return upcoming_df

    mask = ~upcoming_df.apply(
        lambda row: (row["home_team"], row["away_team"]) in excluded_pairs,
        axis=1,
    )
    return upcoming_df[mask].copy()


def _parse_utc_datetime(iso_date: str | datetime) -> datetime:
    if hasattr(iso_date, "to_pydatetime"):
        dt = iso_date.to_pydatetime()
    elif isinstance(iso_date, str):
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    else:
        dt = iso_date
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone()


_WINDOWS_TZ_ABBREVS = {
    "Coordinated Universal Time": "UTC",
    "Greenwich Mean Time": "GMT",
    "Pacific Standard Time": "PST",
    "Pacific Daylight Time": "PDT",
    "US Mountain Standard Time": "MST",
    "Mountain Standard Time": "MST",
    "Mountain Daylight Time": "MDT",
    "Central Standard Time": "CST",
    "Central Daylight Time": "CDT",
    "Eastern Standard Time": "EST",
    "Eastern Daylight Time": "EDT",
    "Atlantic Standard Time": "AST",
    "Atlantic Daylight Time": "ADT",
    "Alaskan Standard Time": "AKST",
    "Alaskan Daylight Time": "AKDT",
    "Hawaiian Standard Time": "HST",
    "GMT Standard Time": "GMT",
    "GMT Daylight Time": "BST",
    "W. Europe Standard Time": "CET",
    "Central Europe Standard Time": "CET",
    "Central European Standard Time": "CET",
    "Romance Standard Time": "CET",
    "SE Asia Standard Time": "ICT",
    "Singapore Standard Time": "SGT",
    "Tokyo Standard Time": "JST",
    "Korea Standard Time": "KST",
    "China Standard Time": "CST",
    "AUS Eastern Standard Time": "AEST",
    "AUS Eastern Daylight Time": "AEDT",
    "India Standard Time": "IST",
}


def _compact_offset(dt: datetime) -> str:
    offset = dt.utcoffset()
    if offset is None:
        return "LOCAL"
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    if minutes:
        return f"GMT{sign}{hours}:{minutes:02d}"
    return f"GMT{sign}{hours}"


def _local_tz_label(dt: datetime) -> str:
    for candidate in (dt.strftime("%Z"), dt.tzname()):
        if candidate and len(candidate) <= 5 and candidate != "%%Z":
            return candidate
        if candidate in _WINDOWS_TZ_ABBREVS:
            return _WINDOWS_TZ_ABBREVS[candidate]

    is_dst = dt.dst() is not None and dt.dst() != timedelta(0)
    if time.daylight:
        system_abbr = time.tzname[1 if is_dst else 0]
        if system_abbr:
            return system_abbr

    return _compact_offset(dt)


def format_kickoff(iso_date: str | datetime) -> str:
    local_dt = _parse_utc_datetime(iso_date)
    hour = int(local_dt.strftime("%I"))
    clock = f"{hour}:{local_dt.strftime('%M %p')}"
    return f"{local_dt.strftime('%a %b %d')} · {clock} {_local_tz_label(local_dt)}"


def format_date_local(iso_date: str | datetime) -> str:
    return _parse_utc_datetime(iso_date).strftime("%B %d, %Y")


def status_badge(status: str) -> str:
    labels = {
        "NS": "Upcoming",
        "1H": "1st Half",
        "HT": "Half Time",
        "2H": "2nd Half",
        "ET": "Extra Time",
        "P": "Penalties",
        "BT": "Break",
        "LIVE": "Live",
        "FT": "Full Time",
        "AET": "After Extra Time",
        "PEN": "Penalties",
    }
    return labels.get(status, status)


def fixture_home_team(fixture: dict) -> str:
    return resolve_team_name(fixture["teams"]["home"]["name"])


def fixture_away_team(fixture: dict) -> str:
    return resolve_team_name(fixture["teams"]["away"]["name"])


def fixture_score(fixture: dict) -> tuple[int | None, int | None]:
    goals = fixture.get("goals") or {}
    return goals.get("home"), goals.get("away")


def fixture_penalty_score(fixture: dict) -> tuple[int | None, int | None]:
    penalty = (fixture.get("score") or {}).get("penalty") or {}
    home, away = penalty.get("home"), penalty.get("away")
    if home is None or away is None:
        return None, None
    return int(home), int(away)


def fixture_regular_time_score(fixture: dict) -> tuple[int | None, int | None]:
    score = fixture.get("score") or {}
    fulltime = score.get("fulltime") or {}
    extratime = score.get("extratime") or {}

    if fulltime.get("home") is not None and fulltime.get("away") is not None:
        return int(fulltime["home"]), int(fulltime["away"])
    if extratime.get("home") is not None and extratime.get("away") is not None:
        return int(extratime["home"]), int(extratime["away"])
    return fixture_score(fixture)


def fixture_score_lines(fixture: dict) -> tuple[str, str | None]:
    status = fixture["fixture"]["status"]["short"]
    pen_home, pen_away = fixture_penalty_score(fixture)
    has_penalties = pen_home is not None and pen_away is not None

    if status in {"P", "PEN"} or has_penalties:
        reg_home, reg_away = fixture_regular_time_score(fixture)
        if reg_home is None or reg_away is None:
            main_score = "vs"
        else:
            main_score = f"{reg_home} – {reg_away}"
        pen_score = f"({pen_home} – {pen_away})" if has_penalties else None
        return main_score, pen_score

    home_goals, away_goals = fixture_score(fixture)
    if home_goals is not None and away_goals is not None:
        return f"{home_goals} – {away_goals}", None
    return "vs", None


def split_api_fixtures(fixtures: dict) -> tuple[list[dict], list[dict]]:
    upcoming, completed = [], []
    matches = fixtures.get("matches") or []
    for match in matches:
        if match.get("status") in ["TIMED", "SCHEDULED", "POSTPONED"]:
            upcoming.append(match)
        elif match.get("status") in ["FINISHED", "CANCELLED", "SUSPENDED"]:
            completed.append(match)
    return upcoming, completed


def parse_finished_match_scores(fixtures: dict) -> pd.DataFrame:
    rows = []
    for match in fixtures.get("matches") or []:
        if match.get("status") not in {"FINISHED", "AWARDED"}:
            continue
        score = match.get("score") or {}
        full_time = score.get("fullTime") or {}
        home_goals = full_time.get("home")
        away_goals = full_time.get("away")
        if home_goals is None or away_goals is None:
            continue
        rows.append(
            {
                "home_team": fd_match_home_team(match),
                "away_team": fd_match_away_team(match),
                "actual_home_goals": int(home_goals),
                "actual_away_goals": int(away_goals),
            }
        )

    columns = ["home_team", "away_team", "actual_home_goals", "actual_away_goals"]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows)


def fd_match_home_team(match: dict) -> str:
    return resolve_team_name((match.get("homeTeam") or {}).get("name", ""))


def fd_match_away_team(match: dict) -> str:
    return resolve_team_name((match.get("awayTeam") or {}).get("name", ""))


def fd_match_round_name(match: dict) -> str:
    group = match.get("group")
    if group:
        return group.replace("GROUP_", "Group ").replace("_", " ")

    stage_labels = {
        "GROUP_STAGE": "Group Stage",
        "LAST_16": "Round of 16",
        "QUARTER_FINALS": "Quarter-finals",
        "SEMI_FINALS": "Semi-finals",
        "THIRD_PLACE": "Third place",
        "FINAL": "Final",
    }
    stage = match.get("stage") or ""
    return stage_labels.get(stage, stage.replace("_", " ").title())


def fd_match_score_lines(match: dict) -> tuple[str, str | None]:
    score = match.get("score") or {}
    full_time = score.get("fullTime") or {}
    home = full_time.get("home")
    away = full_time.get("away")

    if home is None or away is None:
        return "vs", None

    main_score = f"{int(home)} – {int(away)}"
    penalties = score.get("penalties") or {}
    pen_home = penalties.get("home")
    pen_away = penalties.get("away")
    if pen_home is not None and pen_away is not None:
        return main_score, f"({int(pen_home)} – {int(pen_away)})"
    return main_score, None


def fd_status_badge(status: str) -> str:
    labels = {
        "TIMED": "Upcoming",
        "SCHEDULED": "Upcoming",
        "POSTPONED": "Postponed",
        "FINISHED": "Full Time",
        "AWARDED": "Awarded",
        "CANCELLED": "Cancelled",
        "SUSPENDED": "Suspended",
        "IN_PLAY": "Live",
        "PAUSED": "Half Time",
    }
    return labels.get(status, status.replace("_", " ").title())
