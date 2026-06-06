"""Load and format tournament prediction results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from utils.matches import format_kickoff
from utils.teams import resolve_team_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "FIFA World Cup 2026 - DataCamp Competition" / "results"
GROUP_PREDICTIONS_CSV = RESULTS_DIR / "final_group_predictions.csv"
KNOCKOUT_PREDICTIONS_CSV = RESULTS_DIR / "final_knockout_predictions.csv"

_COMMON_COLUMNS = [
    "match_id",
    "stage",
    "group",
    "round",
    "home_team",
    "away_team",
    "date_utc",
    "venue",
    "predicted_home_goals",
    "predicted_away_goals",
    "corners",
    "yellow_cards",
    "red_cards",
    "winner",
    "penalties",
]


@st.cache_data(show_spinner=False)
def load_group_predictions() -> pd.DataFrame:
    df = pd.read_csv(GROUP_PREDICTIONS_CSV)
    df["date_utc"] = pd.to_datetime(df["date_utc"], utc=True)
    df["home_team"] = df["home_team"].map(resolve_team_name)
    df["away_team"] = df["away_team"].map(resolve_team_name)
    df["stage"] = "group"
    df["round"] = "Group " + df["group"].astype(str)
    df["winner"] = df["winning_team"]
    df["penalties"] = False
    return df[_COMMON_COLUMNS].sort_values("date_utc").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_knockout_predictions() -> pd.DataFrame:
    df = pd.read_csv(KNOCKOUT_PREDICTIONS_CSV)
    df["date_utc"] = pd.to_datetime(df["date_utc"], utc=True)
    df["home_team"] = df["predicted_home_team"].map(resolve_team_name)
    df["away_team"] = df["predicted_away_team"].map(resolve_team_name)
    df["stage"] = "knockout"
    df["group"] = pd.NA
    df["winner"] = df["match_winner"]
    return df[_COMMON_COLUMNS].sort_values("date_utc").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_all_predictions() -> pd.DataFrame:
    return pd.concat(
        [load_group_predictions(), load_knockout_predictions()],
        ignore_index=True,
    ).sort_values("date_utc").reset_index(drop=True)


def format_predicted_score(row: pd.Series) -> str:
    return f"{int(row['predicted_home_goals'])}–{int(row['predicted_away_goals'])}"


def format_actual_score(row: pd.Series) -> str:
    return f"{int(row['actual_home_goals'])}–{int(row['actual_away_goals'])}"


def _match_outcome(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "home"
    if away_goals > home_goals:
        return "away"
    return "draw"


def build_score_comparison(predictions: pd.DataFrame, actual: pd.DataFrame) -> pd.DataFrame:
    if predictions.empty or actual.empty:
        return pd.DataFrame()

    merged = predictions.merge(actual, on=["home_team", "away_team"], how="inner")
    if merged.empty:
        return merged

    merged["actual_outcome"] = merged.apply(
        lambda row: _match_outcome(row["actual_home_goals"], row["actual_away_goals"]),
        axis=1,
    )
    merged["exact_score"] = (
        (merged["predicted_home_goals"] == merged["actual_home_goals"])
        & (merged["predicted_away_goals"] == merged["actual_away_goals"])
    )
    merged["result_match"] = merged["winner"] == merged["actual_outcome"]
    merged["goal_error"] = (
        (merged["predicted_home_goals"] - merged["actual_home_goals"]).abs()
        + (merged["predicted_away_goals"] - merged["actual_away_goals"]).abs()
    )
    return merged.sort_values("date_utc").reset_index(drop=True)


def apply_prediction_filters(
    predictions: pd.DataFrame,
    *,
    stage_filter: str,
    group_filter: list[str],
    round_filter: list[str],
) -> pd.DataFrame:
    filtered = predictions.copy()
    if stage_filter == "Group stage":
        filtered = filtered[filtered["stage"] == "group"]
    elif stage_filter == "Knockout":
        filtered = filtered[filtered["stage"] == "knockout"]
    if group_filter:
        filtered = filtered[filtered["group"].isin(group_filter)]
    if round_filter:
        filtered = filtered[filtered["round"].isin(round_filter)]
    return filtered.reset_index(drop=True)


def format_penalties(value: object) -> str:
    if pd.isna(value):
        return "—"
    return "Yes" if value else "No"


def format_winner(row: pd.Series) -> str:
    winner = row["winner"]
    if winner == "home":
        return row["home_team"]
    if winner == "away":
        return row["away_team"]
    if winner == "draw":
        return "Draw"
    return str(winner)


def prepare_display_frame(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()
    display["Kickoff"] = display["date_utc"].map(format_kickoff)
    display["Score"] = display.apply(format_predicted_score, axis=1)
    display["Winner"] = display.apply(format_winner, axis=1)
    display["Penalties"] = display["penalties"].map(format_penalties)
    display["Cards"] = display.apply(
        lambda row: f"{int(row['yellow_cards'])} / {int(row['red_cards'])}",
        axis=1,
    )
    return display
