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
MONTE_CARLO_PREDICTIONS_CSV = RESULTS_DIR / "monte_carlo_results.csv"
MONTE_CARLO_TEAM_MATCHUPS_CSV = RESULTS_DIR / "monte_carlo_team_matchups.csv"

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
def load_monte_carlo_predictions() -> pd.DataFrame:
    df = pd.read_csv(MONTE_CARLO_PREDICTIONS_CSV)
    df = df.rename(
        columns={
            "Team": "team",
            "Rating": "rating",
            "Champion": "champion",
            "Runner-Up": "runner_up",
            "3rd Place": "third_place",
            "Podium": "podium",
            "Win %": "win_percent",
            "Pod %": "podium_percent",
        }
    )
    df["team"] = df["team"].map(resolve_team_name)
    return df.sort_values("win_percent", ascending=False).reset_index(drop=True)

@st.cache_data(show_spinner=False)
def load_monte_carlo_team_matchups() -> pd.DataFrame:
    df = pd.read_csv(MONTE_CARLO_TEAM_MATCHUPS_CSV)
    df = df.rename(
        columns={
            "Team A": "team_a",
            "Team B": "team_b",
            "Matchup Count": "matchup_count",
            "Matchup %": "matchup_percent",
        }
    )
    df["team_a"] = df["team_a"].map(resolve_team_name)
    df["team_b"] = df["team_b"].map(resolve_team_name)
    return df.sort_values("matchup_percent", ascending=False).reset_index(drop=True)


def monte_carlo_matchup_total_sims(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    return int(df["matchup_count"].max())


def lookup_monte_carlo_matchup(
    df: pd.DataFrame,
    team_a: str,
    team_b: str,
    *,
    total_sims: int | None = None,
) -> tuple[float, int]:
    if team_a == team_b or df.empty:
        return 0.0, 0
    first, second = sorted([team_a, team_b])
    match = df[(df["team_a"] == first) & (df["team_b"] == second)]
    if match.empty:
        return 0.0, 0
    row = match.iloc[0]
    count = int(row["matchup_count"])
    if total_sims and total_sims > 0:
        return round(count / total_sims * 100, 1), count
    return float(row["matchup_percent"]), count


def monte_carlo_total_simulations(df: pd.DataFrame) -> int:
    return int(df["champion"].sum())


def monte_carlo_tier(win_percent: float) -> str:
    if win_percent >= 5:
        return "Title heavyweight"
    if win_percent >= 2:
        return "Outside contender"
    if win_percent >= 0.5:
        return "Dark horse"
    if win_percent > 0:
        return "Long shot"
    return "Miracle run"


def team_champion_narrative(row: pd.Series, total_sims: int) -> str:
    team = row["team"]
    wins = int(row["champion"])
    runner_up = int(row["runner_up"])
    third = int(row["third_place"])
    win_pct = row["win_percent"]
    podium_pct = row["podium_percent"]

    if win_pct >= 5:
        opener = f"{team} enter the tournament as genuine title favourites."
    elif win_pct >= 2:
        opener = f"{team} belong in the conversation — not the top pick, but very much in the mix."
    elif win_pct >= 0.5:
        opener = f"{team} are a live dark horse: the model gives them a puncher's chance."
    elif win_pct > 0:
        opener = f"{team} would need a fairytale run, but the simulator still sees a glimmer of hope."
    else:
        opener = f"{team} never reached the summit in {total_sims:,} simulated tournaments."

    if win_pct > 0:
        body = (
            f" Across {total_sims:,} knock-out simulations they lifted the trophy "
            f"{wins:,} times ({win_pct:.1f}%), finished runners-up "
            f"{runner_up:,} times, and took third {third:,} times "
            f"— a podium finish in {podium_pct:.1f}% of runs."
        )
    else:
        body = f" Their Elo rating of {int(row['rating'])} kept them on the outside looking in."
    return opener + body


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
