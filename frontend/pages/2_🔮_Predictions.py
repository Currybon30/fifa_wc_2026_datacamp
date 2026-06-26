import streamlit as st

from utils.matches import fetch_api_fixtures, get_football_data_key, parse_finished_match_scores
from utils.predictions import apply_prediction_filters, build_score_comparison, load_all_predictions, load_monte_carlo_predictions, load_monte_carlo_team_matchups
from utils.ui import (
    inject_base_styles,
    render_copyright_footer,
    render_monte_carlo_champion_stats,
    render_monte_carlo_team_matchups,
    render_prediction_card,
)

st.set_page_config(page_title="Predictions", page_icon="🔮", layout="wide")

inject_base_styles()


st.title("🔮 Predictions")
st.caption("AI-integrated prediction system for the FIFA World Cup 2026")
st.caption("***Predictions are for reference purposes only. We do not guarantee the accuracy.***")


predictions = load_all_predictions()

with st.sidebar:
    previous_matches_include = st.checkbox("Include previous matches", value=False)
    stage_filter = st.selectbox(
        "Stage",
        options=["All", "Group stage", "Knockout"],
        index=0,
    )
    
    group_options = sorted(predictions["group"].dropna().unique())
    group_filter = st.multiselect("Filter by group", options=group_options, default=[])
    round_options = sorted(predictions.loc[predictions["stage"] == "knockout", "round"].unique())
    round_filter = st.multiselect("Filter by knockout round", options=round_options, default=[])
    limit = st.slider("Matches to show", min_value=5, max_value=len(predictions), value=min(20, len(predictions)), step=5)

scoped = apply_prediction_filters(
    predictions,
    stage_filter=stage_filter,
    group_filter=group_filter,
    round_filter=round_filter,
    previous_matches_include=previous_matches_include,
)
filtered = scoped.head(limit)

if filtered.empty:
    st.info("No predictions match the selected filters.")
else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Matches shown", len(filtered))
    col2.metric("Avg goals / match", f"{(filtered['predicted_home_goals'] + filtered['predicted_away_goals']).mean():.1f}")
    col3.metric("Avg corners / match", f"{filtered['corners'].mean():.1f}")
    col4.metric("Avg cards / match", f"{(filtered['yellow_cards'] + filtered['red_cards']).mean():.1f}")


    tab_scores, tab_corners, tab_cards, tab_champion_stats, tab_team_matchups= st.tabs(
        ["🥅 Goals", "🚩 Corners", "🟡 - 🔴 Cards", "🏅 Champion stats", "🤜🤛 Team Matchups"]
    )

    with tab_scores:
        for _, row in filtered.iterrows():
            render_prediction_card(row, variant="scores")

    with tab_corners:
        for _, row in filtered.iterrows():
            render_prediction_card(row, variant="corners")

    with tab_cards:
        for _, row in filtered.iterrows():
            render_prediction_card(row, variant="cards")

    with tab_champion_stats:
        render_monte_carlo_champion_stats(load_monte_carlo_predictions())

    with tab_team_matchups:
        render_monte_carlo_team_matchups(load_monte_carlo_team_matchups())

render_copyright_footer()
