import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from utils.predictions import (GROUP_PREDICTIONS_CSV, KNOCKOUT_PREDICTIONS_CSV,
                               load_monte_carlo_predictions)
from utils.teams import (all_teams_from_fixtures, is_slot_team,
                         resolve_team_name)
from utils.ui import inject_base_styles, render_copyright_footer

WC_GREEN = "#1a5f4a"
WC_GREEN_LIGHT = "#2d8659"
WC_ACCENT = "#0b3d2e"
WC_YELLOW = "#f5b041"
WC_RED = "#c0392b"
PLOT_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif"),
    margin=dict(l=20, r=20, t=40, b=20),
)

COMPETITION_DIR = (
    Path(__file__).resolve().parents[2] /
    "FIFA World Cup 2026 - DataCamp Competition"
)
if str(COMPETITION_DIR) not in sys.path:
    sys.path.insert(0, str(COMPETITION_DIR))

HISTORICAL_STAT_CSV = COMPETITION_DIR / "data" / "history_stat.csv"
ELO_RATINGS_CSV = COMPETITION_DIR / "data" / "elo.csv"
PREDICTION_ACTUAL_GROUP_CSV = COMPETITION_DIR / "results" / "group_fixtures_actual.csv"
# PREDICTION_ACTUAL_KNOCKOUT_CSV = COMPETITION_DIR / "results" /

st.set_page_config(page_title="Analysis", page_icon="📈", layout="wide")

inject_base_styles()


st.title("📈 Analysis")
st.caption("Team form, Elo ratings, and historical World Cup statistics.")


HISTORICAL_STAT = pd.read_csv(HISTORICAL_STAT_CSV)
ELO_RATINGS = pd.read_csv(ELO_RATINGS_CSV)
GROUP_PREDICTIONS = pd.read_csv(GROUP_PREDICTIONS_CSV)
KNOCKOUT_PREDICTIONS = pd.read_csv(KNOCKOUT_PREDICTIONS_CSV)
PREDICTION_ACTUAL_GROUP = pd.read_csv(PREDICTION_ACTUAL_GROUP_CSV)
# PREDICTION_ACTUAL_KNOCKOUT = pd.read_csv(PREDICTION_ACTUAL_KNOCKOUT_CSV)
MONTE_CARLO_PREDICTIONS = load_monte_carlo_predictions()

GROUP_PREDICTIONS["home_team"] = GROUP_PREDICTIONS["home_team"].apply(
    resolve_team_name)
GROUP_PREDICTIONS["away_team"] = GROUP_PREDICTIONS["away_team"].apply(
    resolve_team_name)
KNOCKOUT_PREDICTIONS["predicted_home_team"] = KNOCKOUT_PREDICTIONS["predicted_home_team"].apply(
    resolve_team_name)
KNOCKOUT_PREDICTIONS["predicted_away_team"] = KNOCKOUT_PREDICTIONS["predicted_away_team"].apply(
    resolve_team_name)

ALL_PREDICTIONS = pd.concat(
    [
        GROUP_PREDICTIONS.assign(stage="Group"),
        KNOCKOUT_PREDICTIONS.rename(
            columns={"predicted_home_team": "home_team",
                     "predicted_away_team": "away_team"}
        ).assign(stage="Knockout", group=pd.NA),
    ],
    ignore_index=True,
)
ALL_PREDICTIONS["total_goals"] = (
    ALL_PREDICTIONS["predicted_home_goals"] +
    ALL_PREDICTIONS["predicted_away_goals"]
)
ALL_PREDICTIONS["total_cards"] = (
    ALL_PREDICTIONS["yellow_cards"] + ALL_PREDICTIONS["red_cards"]
)

WC_TEAMS = [t for t in all_teams_from_fixtures() if not is_slot_team(t)]
ELO_RATINGS["Team"] = ELO_RATINGS["Team"].apply(resolve_team_name)
wc_elo = (
    ELO_RATINGS[ELO_RATINGS["Team"].isin(WC_TEAMS)]
    .sort_values("Elo", ascending=True)
    .tail(20)
)

HISTORICAL_STAT["date"] = pd.to_datetime(HISTORICAL_STAT["date"])
wc_history = HISTORICAL_STAT[HISTORICAL_STAT["tournament"]
                             == "FIFA World Cup"].copy()
wc_history = wc_history.dropna(subset=["home_score", "away_score"])
wc_history["year"] = wc_history["date"].dt.year
wc_history["total_goals"] = wc_history["home_score"] + wc_history["away_score"]
goals_by_year = (
    wc_history.groupby("year")
    .agg(matches=("total_goals", "count"), avg_goals=("total_goals", "mean"))
    .reset_index()
    .sort_values("year")
)

tab_elo, tab_history, tab_predictions, tab_comparison_charts = st.tabs(
    ["⭐ Elo ratings", "📜 World Cup history", "🔮 WC26 predictions", "📊 Comparison charts"]
)

with tab_elo:
    st.subheader("Top Elo ratings — World Cup 2026 teams")
    st.caption("Highest-rated teams among confirmed tournament participants.")
    if wc_elo.empty:
        st.info("No Elo data matched current fixture teams.")
    else:
        fig_elo = px.bar(
            wc_elo,
            x="Elo",
            y="Team",
            orientation="h",
            color="Elo",
            color_continuous_scale=["#c8e6d4", WC_GREEN, WC_ACCENT],
        )
        fig_elo.update_layout(
            **PLOT_LAYOUT,
            height=520,
            showlegend=False,
            coloraxis_showscale=False,
            xaxis_title="Elo rating",
            yaxis_title="",
        )
        st.plotly_chart(fig_elo, width='stretch')

with tab_history:
    st.subheader("Goals per match at past World Cups")
    st.caption("Average total goals scored per game, by tournament year.")
    fig_history = px.line(
        goals_by_year,
        x="year",
        y="avg_goals",
        markers=True,
        labels={"year": "Tournament year", "avg_goals": "Avg goals / match"},
    )
    fig_history.update_traces(
        line_color=WC_GREEN, marker=dict(size=8, color=WC_GREEN_LIGHT))
    fig_history.update_layout(
        **PLOT_LAYOUT, height=400, yaxis=dict(range=[0, None]))
    st.plotly_chart(fig_history, width='stretch')

    col_l, col_r = st.columns(2)
    with col_l:
        st.metric("World Cup matches in dataset", f"{len(wc_history):,}")
    with col_r:
        st.metric("All-time avg goals / match",
                  f"{wc_history['total_goals'].mean():.2f}")

with tab_predictions:
    st.caption(
        "The prediction analysis is for reference only. The predictions are not guaranteed to be accurate.")
    st.subheader("Predicted goals by group stage group")
    group_goals = (
        GROUP_PREDICTIONS.assign(
            total_goals=lambda d: d["predicted_home_goals"] +
            d["predicted_away_goals"]
        )
        .groupby("group", as_index=False)["total_goals"]
        .mean()
        .sort_values("group")
    )
    fig_group = px.bar(
        group_goals,
        x="group",
        y="total_goals",
        color="group",
        labels={"group": "Group", "total_goals": "Avg predicted goals / match"},
    )
    fig_group.update_layout(
        **PLOT_LAYOUT,
        height=360,
        showlegend=False,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_group, width='stretch')

    st.divider()

    st.subheader("Predicted match statistics - Goals")
    stage_stats = (
        ALL_PREDICTIONS.groupby("stage")
        .agg(
            avg_goals=("total_goals", "mean"),
        )
        .reset_index()
        .assign(stage=lambda d: d["stage"].str.title())
        .rename(
            columns={
                "avg_goals": "Goals",
            }
        )
    )
    fig_stats = px.bar(
        stage_stats.melt(id_vars="stage", var_name="metric",
                         value_name="value"),
        x="stage",
        y="value",
        color="metric",
        barmode="group",
        color_discrete_map={
            "Goals": WC_GREEN
        },
        labels={
            "stage": "Stage",
            "value": "Average per match",
            "metric": "Metric",
        },
    )
    fig_stats.update_layout(**PLOT_LAYOUT, height=380, legend_title="")
    st.plotly_chart(fig_stats, width='stretch')

    st.divider()
    st.subheader("Predicted goals by home - away teams")
    home_away_goals = (
        ALL_PREDICTIONS.groupby("stage")
        .agg(
            avg_home_goals=("predicted_home_goals", "mean"),
            avg_away_goals=("predicted_away_goals", "mean"),
        )
        .reset_index()
        .rename(
            columns={
                "avg_home_goals": "Home goals",
                "avg_away_goals": "Away goals",
            }
        )
    )
    fig_home_away = px.bar(
        home_away_goals.melt(
            id_vars="stage", var_name="metric", value_name="value"),
        x="stage",
        y="value",
        color="metric",
        barmode="group",
        color_discrete_map={
            "Home goals": WC_GREEN,
            "Away goals": WC_GREEN_LIGHT,
        },
        labels={
            "stage": "Stage",
            "value": "Average per match",
            "metric": "Metric",
        },
    )
    fig_home_away.update_layout(**PLOT_LAYOUT, height=380, legend_title="")
    st.plotly_chart(fig_home_away, width='stretch')

    st.divider()
    st.subheader("Predicted yellow and red cards by stage")
    card_stats = (
        ALL_PREDICTIONS.groupby("stage")
        .agg(
            avg_yellow_cards=("yellow_cards", "mean"),
            avg_red_cards=("red_cards", "mean"),
        )
        .reset_index()
        .assign(stage=lambda d: d["stage"].str.title())
        .rename(
            columns={
                "avg_yellow_cards": "Yellow cards",
                "avg_red_cards": "Red cards",
            }
        )
    )
    fig_card = px.bar(
        card_stats.melt(id_vars="stage", var_name="metric",
                        value_name="value"),
        x="stage",
        y="value",
        color="metric",
        barmode="group",
        color_discrete_map={
            "Yellow cards": WC_YELLOW,
            "Red cards": WC_RED,
        },
        labels={
            "stage": "Stage",
            "value": "Average per match",
            "metric": "Card type",
        },
    )
    fig_card.update_layout(**PLOT_LAYOUT, height=380, legend_title="")
    st.plotly_chart(fig_card, width='stretch')

    st.divider()
    st.subheader("Predicted corners by stage")
    corner_stats = (
        ALL_PREDICTIONS.groupby("stage")
        .agg(
            avg_corners=("corners", "mean"),
        )
        .reset_index()
        .rename(
            columns={
                "avg_corners": "Corners",
            }
        )
    )
    fig_corner = px.bar(
        corner_stats.melt(id_vars="stage", var_name="metric",
                          value_name="value"),
        x="stage",
        y="value",
        color="metric",
        barmode="group",
        color_discrete_map={
            "Corners": WC_GREEN_LIGHT,
        },
        labels={
            "stage": "Stage",
            "value": "Average per match",
            "metric": "Metric",
        },
    )
    fig_corner.update_layout(**PLOT_LAYOUT, height=380, legend_title="")
    st.plotly_chart(fig_corner, width='stretch')

    st.divider()
    st.subheader("Elo ratings and Win Percentage by teams in WC26 predictions")
    fig_elo_win = px.scatter(
        MONTE_CARLO_PREDICTIONS,
        x="rating",
        y="win_percent",
        color="team",
        labels={
            "rating": "Elo rating",
            "win_percent": "Win %",
            "team": "Team",
        }
    )
    fig_elo_win.update_layout(**PLOT_LAYOUT, height=380, legend_title="")
    st.plotly_chart(fig_elo_win, width='stretch')
with tab_comparison_charts:
    st.subheader("Comparison of predicted (2K and 50K simulations) vs actual statistics")
    st.warning("Charts are available once the tournament finishes. Please check back later.")
    tab_group_stage, tab_knockout_stage = st.tabs(
        ["Group Stage", "Knockout Stage"]
    )
    with tab_group_stage:
        tab_winners, tab_goals, tab_corners, tab_cards = st.tabs(
        ["Match Winner", "Goals", "Corners", "Cards"]
    )
    with tab_knockout_stage:
        tab_qualified_teams, tab_winners, tab_goals, tab_corners, tab_cards, tab_penalties = st.tabs(
        ["Qualified Teams", "Match Winner", "Goals", "Corners", "Cards", "Penalties"]
    )
    


render_copyright_footer()
