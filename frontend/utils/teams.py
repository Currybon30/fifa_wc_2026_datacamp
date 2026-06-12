"""Team names and static flag assets for World Cup 2026."""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

COMPETITION_DIR = (
    Path(__file__).resolve().parents[2] / "FIFA World Cup 2026 - DataCamp Competition"
)
if str(COMPETITION_DIR) not in sys.path:
    sys.path.insert(0, str(COMPETITION_DIR))

from feature_engineering import resolve_team_original_to_updated  # noqa: E402

STATIC_FLAGS_DIR = Path(__file__).resolve().parents[1] / "static" / "flags"
LOGO_PLACEHOLDER_URL = "app/static/logo-placeholder.png"
GROUP_FIXTURES_CSV = COMPETITION_DIR / "data" / "group_fixtures.csv"

# Common API / display variants mapped to fixture dataset names.
__FLAG_NAME_ALIASES = {
    "United States": "USA",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Korea Republic": "South Korea",
    "IR Iran": "Iran",
    "Côte D'Ivoire": "Côte d'Ivoire",
}


def resolve_team_name(name: str) -> str:
    return resolve_team_original_to_updated(name)


def flag_team_name(name: str) -> str:
    if name in __FLAG_NAME_ALIASES:
        return __FLAG_NAME_ALIASES[name]
    resolved = resolve_team_name(name)
    return __FLAG_NAME_ALIASES.get(resolved, resolved)


def team_slug(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name) 
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")
    return slug or "unknown"


def all_teams_from_fixtures() -> list[str]:
    df = pd.read_csv(GROUP_FIXTURES_CSV)
    teams = set(df["home_team"]) | set(df["away_team"])
    return sorted(resolve_team_name(t) for t in teams)


def flag_filename(team_name: str) -> str:
    return f"{team_slug(flag_team_name(team_name))}.png"


def flag_file_path(team_name: str) -> Path:
    return STATIC_FLAGS_DIR / flag_filename(team_name)


def is_slot_team(name: str) -> bool:
    """Knockout bracket placeholders (not yet resolved to a team)."""
    return name.startswith(("Winner ", "Runner-up ", "Best 3rd", "Loser "))


def flag_static_url(team_name: str) -> str:
    if is_slot_team(team_name):
        return LOGO_PLACEHOLDER_URL
    path = flag_file_path(team_name)
    if path.exists():
        return f"app/static/flags/{flag_filename(team_name)}"
    return LOGO_PLACEHOLDER_URL
