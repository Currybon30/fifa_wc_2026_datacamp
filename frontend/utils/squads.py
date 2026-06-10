from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SQUADS_FOLDER = (
    PROJECT_ROOT
    / "FIFA World Cup 2026 - DataCamp Competition"
    / "data"
    / "squads"
)

# Squad CSV filenames vs names used elsewhere in the app.
SQUAD_FILE_ALIASES = {
    "Congo DR": "DR Congo",
    "United States": "USA",
}

_squads: dict[str, pd.DataFrame] = {}


def _file_team_from_display(display_name: str) -> str:
    reverse = {display: file_name for file_name, display in SQUAD_FILE_ALIASES.items()}
    return reverse.get(display_name, display_name)


def _display_team(file_team: str) -> str:
    return SQUAD_FILE_ALIASES.get(file_team, file_team)


def _load_squads() -> dict[str, pd.DataFrame]:
    if _squads:
        return _squads

    for file in SQUADS_FOLDER.glob("*.csv"):
        file_team = file.stem.split("-", 2)[-1]
        _squads[file_team] = pd.read_csv(file)
    return _squads


def list_squad_teams() -> list[str]:
    return sorted(_display_team(team) for team in _load_squads())


def resolve_squad_df(squad_df: pd.DataFrame) -> pd.DataFrame:
    squad_df = squad_df.copy()
    if "#" in squad_df.columns:
        squad_df = squad_df.drop(columns=["#"])
    return squad_df.rename(
        columns={
            "POS": "position",
            "PLAYER NAME": "player_name",
            "FIRST NAME(S)": "first_name",
            "LAST NAME(S)": "last_name",
            "NAME ON SHIRT": "name_on_shirt",
            "DOB": "dob",
            "CLUB": "club",
            "HEIGHT (CM)": "height",
            "NATIONALITY": "nationality",
        }
    )


def get_squad(team_name: str) -> pd.DataFrame:
    squads = _load_squads()
    file_team = _file_team_from_display(team_name)
    if file_team not in squads:
        raise KeyError(f"No squad data for {team_name}")
    return resolve_squad_df(squads[file_team])


def split_squad_players_coach(
    squad_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series | None]:
    coach_mask = squad_df["position"].astype(str).str.contains("coach", case=False, na=False)
    coach_rows = squad_df[coach_mask]
    players = squad_df[~coach_mask].reset_index(drop=True)
    coach = coach_rows.iloc[0] if len(coach_rows) else None
    return players, coach


def coach_display_name(coach: pd.Series) -> str:
    parts = [
        str(value).strip()
        for value in (coach.get("last_name"), coach.get("first_name"))
        if pd.notna(value) and str(value).strip()
    ]
    if parts:
        return " ".join(parts)
    if pd.notna(coach.get("player_name")) and str(coach.get("player_name")).strip():
        return str(coach["player_name"]).strip()
    return "Head coach"
