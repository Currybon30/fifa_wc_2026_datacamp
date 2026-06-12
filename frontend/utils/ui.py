"""Shared Streamlit UI helpers."""

from datetime import datetime
import html
from re import L
import textwrap

import streamlit as st

from utils.teams import flag_file_path
from utils.standings import STANDINGS_TABLE_HEIGHT, TEAMS_PER_GROUP
from utils.squads import get_squad


def render_html(body: str) -> None:
    st.markdown(textwrap.dedent(body).strip(), unsafe_allow_html=True)


def _show_team_flag(team_name: str, *, width: int = 56) -> None:
    path = flag_file_path(team_name)
    if path.exists():
        st.image(str(path), width=width)
    else:
        st.markdown("🏳️")


def inject_base_styles() -> None:
    render_html(
        """
        <style>
        .wc-hero {
            background: linear-gradient(135deg, #0b3d2e 0%, #1a5f4a 45%, #2d8659 100%);
            border-radius: 16px;
            padding: 2rem 2.5rem;
            color: white;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
        }
        .wc-hero-content {
            flex: 1;
        }
        .wc-hero-logo {
            width: 96px;
            height: 96px;
            object-fit: contain;
            flex-shrink: 0;
        }
        .wc-hero h1 {
            margin: 0 0 0.5rem 0;
            font-size: 2.4rem;
        }
        .wc-hero p {
            margin: 0;
            opacity: 0.92;
            font-size: 1.05rem;
        }
        .wc-card {
            border: 1px solid #e6e6e6;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
            background: rgba(260, 260, 260, 0.75);
        }
        .wc-card-live {
            border-left: 4px solid #e63946;
            background: rgba(260, 260, 260, 0.75);
        }
        .wc-badge {
            display: inline-block;
            padding: 0.15rem 0.55rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }
        .wc-badge-live { background: #ffe0e0; color: #c1121f; }
        .wc-badge-upcoming { background: #e8f4fd; color: #1d4ed8; }
        .wc-badge-finished { background: #ececec; color: #444; }
        .wc-badge-exact { background: #d1fae5; color: #065f46; }
        .wc-badge-miss { background: #fef3c7; color: #92400e; }
        .wc-match-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin: 0.75rem 0;
        }
        .wc-team {
            flex: 1;
            display: flex;
            align-items: center;
            gap: 0.55rem;
            font-weight: 600;
            font-size: 1.05rem;
        }
        .wc-team-home { justify-content: flex-start; }
        .wc-team-away { justify-content: flex-end; }
        .wc-flag {
            width: 28px;
            height: 20px;
            object-fit: cover;
            border-radius: 2px;
            flex-shrink: 0;
        }
        .wc-score {
            min-width: 4rem;
            text-align: center;
            font-size: 1.4rem;
            font-weight: 700;
            color: black;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .wc-score-pens {
            font-size: 0.72rem;
            font-weight: 600;
            color: #666;
            line-height: 1.2;
            margin-top: 0.1rem;
        }
        .wc-meta {
            color: #666;
            font-size: 0.85rem;
            margin-top: 0.35rem;
        }
        .wc-coach-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 55%, #0f3460 100%);
            border-radius: 14px;
            padding: 1.25rem 1.5rem;
            color: #fff;
            margin: 1rem 0 1.5rem 0;
            border-left: 5px solid #e9c46a;
            box-shadow: 0 8px 24px rgba(15, 52, 96, 0.18);
        }
        .wc-coach-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #e9c46a;
            font-weight: 700;
        }
        .wc-coach-name {
            font-size: 1.55rem;
            font-weight: 700;
            margin: 0.35rem 0 0.2rem 0;
            line-height: 1.2;
        }
        .wc-coach-meta {
            font-size: 0.92rem;
            opacity: 0.88;
        }
        .wc-squad-pos-title {
            font-size: 1rem;
            font-weight: 700;
            margin: 1rem 0 0.45rem 0;
            padding-left: 0.65rem;
            border-left: 4px solid var(--wc-pos-color, #1a5f4a);
        }
        .wc-player-card {
            border: 1px solid #e6e6e6;
            border-radius: 12px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.65rem;
            background: rgba(255, 255, 255, 0.82);
            border-top: 3px solid var(--wc-pos-color, #1a5f4a);
            min-height: 160px;
        }
        .wc-player-name {
            font-size: 0.98rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
            line-height: 1.25;
            color: black;
        }
        .wc-player-shirt {
            font-size: 0.78rem;
            color: black;
            margin-bottom: 0.35rem;
        }
        .wc-player-meta {
            font-size: 0.8rem;
            color: black;
            line-height: 1.45;
        }
        .wc-nav-card {
            border: 1px solid #ddd;
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            width: 100%;
            min-height: 168px;
            height: 168px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            background: rgba(260, 260, 260, 0.75);
        }
        .wc-nav-card h3 {
            margin: 0 0 0.5rem 0;
            font-size: 1.1rem;
            color: black;
        }
        .wc-nav-card p {
            margin: 0;
            flex: 1;
            line-height: 1.45;
            color: #444;
        }
        div[data-testid="stHorizontalBlock"]:has(.wc-nav-card) {
            align-items: stretch;
        }
        div[data-testid="stHorizontalBlock"]:has(.wc-nav-card) div[data-testid="column"] {
            display: flex;
            flex-direction: column;
        }
        div[data-testid="stHorizontalBlock"]:has(.wc-nav-card) div[data-testid="column"] > div {
            width: 100%;
        }
        .wc-footer {
            margin-top: 2.5rem;
            padding-top: 1rem;
            border-top: 1px solid #e6e6e6;
            text-align: center;
            color: #888;
            font-size: 0.82rem;
        }
        .wc-podium-favourite-marker {
            display: none;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.wc-podium-favourite-marker) {
            border-width: 3px !important;
            border-color: #d4af37 !important;
            box-shadow: 0 10px 28px rgba(212, 175, 55, 0.22);
        }
        </style>
        """
    )


def render_copyright_footer() -> None:
    year = datetime.now().year
    if year == 2026:
        render_html(
            """
            <div class="wc-footer">
                © 2026 Tuong Nguyen Pham - FIFA World Cup 2026 Prediction System. All rights reserved.
            </div>
            """
        )
    else:
        render_html(
            f"""
            <div class="wc-footer">
                © 2026 - {year} Tuong Nguyen Pham - FIFA World Cup 2026 Prediction System. All rights reserved.
            </div>
            """
        )


def _team_cell(team_name: str, *, away: bool = False) -> str:
    from utils.teams import flag_static_url

    url = flag_static_url(team_name)
    align_class = "wc-team-away" if away else "wc-team-home"
    flag_html = f'<img src="{url}" class="wc-flag" alt="" />'
    if away:
        return f'<div class="wc-team {align_class}"><span style="color: black;">{team_name}</span>{flag_html}</div>'
    return f'<div class="wc-team {align_class}">{flag_html}<span style="color: black;">{team_name}</span></div>'


def render_match_card_api(fixture: dict, *, live: bool = False, localdf = None) -> None:
    if live:
        from utils.matches import (
            fixture_away_team,
            fixture_home_team,
            fixture_score_lines,
            format_kickoff,
            status_badge,
        )

        status = fixture["fixture"]["status"]["short"]
        elapsed = fixture["fixture"]["status"].get("elapsed")
        home = fixture_home_team(fixture)
        away = fixture_away_team(fixture)
        main_score, pen_score = fixture_score_lines(fixture)
        venue = fixture["fixture"].get("venue", {}) or {}
        venue_name = venue.get("name") or "TBD"
        city = venue.get("city") or ""
        location = f"{venue_name}, {city}" if city else venue_name
        round_name = fixture.get("league", {}).get("round") or "Group Stage"

        badge_class = "wc-badge-live" if live else (
            "wc-badge-finished" if status in {"FT", "AET", "PEN"} else "wc-badge-upcoming"
        )
        status_label = status_badge(status)
        if elapsed is not None and live:
            status_label = f"{status_label} · {elapsed}'"

        card_class = "wc-card wc-card-live" if live else "wc-card"
        pen_html = f'<div class="wc-score-pens">{pen_score}</div>' if pen_score else ""
        score_html = f'<div class="wc-score"><div>{main_score}</div>{pen_html}</div>'

        render_html(f"""
            <div class="{card_class}">
                <span class="wc-badge {badge_class}">{status_label}</span>
                <span style="margin-left:0.5rem;color:#666;font-size:0.85rem;">{round_name}</span>
                <div class="wc-match-row">
                    {_team_cell(home)}
                    {score_html}
                    {_team_cell(away, away=True)}
                </div>
                <div class="wc-meta">{format_kickoff(fixture["fixture"]["date"])} · Stadium: {location}</div>
            </div>
            """)
    else:
        from utils.matches import (
            fd_match_away_team,
            fd_match_home_team,
            fd_match_round_name,
            fd_match_score_lines,
            fd_status_badge,
            format_kickoff,
        )

        if localdf is not None:
            match_local = localdf[localdf['date_utc'] == fixture['utcDate']]

        status = fixture.get("status", "")
        home = fd_match_home_team(fixture)
        away = fd_match_away_team(fixture)
        main_score, pen_score = fd_match_score_lines(fixture)
        round_name = fd_match_round_name(fixture)

        badge_class = (
            "wc-badge-finished"
            if status in {"FINISHED", "AWARDED", "CANCELLED", "SUSPENDED"}
            else "wc-badge-upcoming"
        )
        status_label = fd_status_badge(status)
        pen_html = f'<div class="wc-score-pens">{pen_score}</div>' if pen_score else ""
        score_html = f'<div class="wc-score"><div>{main_score}</div>{pen_html}</div>'

        render_html(f"""
            <div class="wc-card">
                <span class="wc-badge {badge_class}">{status_label}</span>
                <span style="margin-left:0.5rem;color:#666;font-size:0.85rem;">{round_name}</span>
                <div class="wc-match-row">
                    {_team_cell(home)}
                    {score_html}
                    {_team_cell(away, away=True)}
                </div>
                <div class="wc-meta">{format_kickoff(fixture["utcDate"])} · Stadium: {match_local["venue"].loc[0]}</div>
            </div>
            """)


def render_match_card_local(row, *, live: bool = False, finished: bool = False) -> None:
    from utils.matches import format_kickoff, status_badge

    if live:
        status = "LIVE"
        badge_class = "wc-badge-live"
        card_class = "wc-card wc-card-live"
    elif finished:
        status = "FT"
        badge_class = "wc-badge-finished"
        card_class = "wc-card"
    else:
        status = "NS"
        badge_class = "wc-badge-upcoming"
        card_class = "wc-card"

    render_html(f"""
        <div class="{card_class}">
            <span class="wc-badge {badge_class}">{status_badge(status)}</span>
            <span style="margin-left:0.5rem;color:#666;font-size:0.85rem;">{row["round"]}</span>
            <div class="wc-match-row">
                {_team_cell(row["home_team"])}
                <div class="wc-score">vs</div>
                {_team_cell(row["away_team"], away=True)}
            </div>
            <div class="wc-meta">{format_kickoff(row["date_utc"])} · Stadium: {row["venue"]}</div>
        </div>
        """)


def render_prediction_card(row, *, variant: str = "scores") -> None:
    from utils.matches import format_kickoff
    from utils.predictions import format_penalties, format_predicted_score, format_winner

    home = row["home_team"]
    away = row["away_team"]
    round_name = row["round"]
    kickoff = format_kickoff(row["date_utc"])
    venue = row["venue"]

    if variant == "scores":
        score = format_predicted_score(row)
        pen_html = ""
        if row["stage"] == "knockout" and bool(row["penalties"]):
            pen_html = '<div class="wc-score-pens">Penalties</div>'
        center_html = f'<div class="wc-score"><div>{score}</div>{pen_html}</div>'
        winner = format_winner(row)
        meta_extra = f" · Winner: {winner}"
    elif variant == "corners":
        center_html = (
            f'<div class="wc-score">'
            f'<div>{int(row["corners"])}</div>'
            f'<div class="wc-score-pens">Corners</div>'
            f"</div>"
        )
        meta_extra = ""
    else:
        center_html = (
            f'<div class="wc-score">'
            f'<div>{int(row["yellow_cards"])} / {int(row["red_cards"])}</div>'
            f'<div class="wc-score-pens">Yellow / Red</div>'
            f"</div>"
        )
        meta_extra = ""

    render_html(f"""
        <div class="wc-card">
            <span class="wc-badge wc-badge-upcoming">Predicted</span>
            <span style="margin-left:0.5rem;color:#666;font-size:0.85rem;">{round_name}</span>
            <div class="wc-match-row">
                {_team_cell(home)}
                {center_html}
                {_team_cell(away, away=True)}
            </div>
            <div class="wc-meta">{kickoff} · Stadium: {venue}{meta_extra}</div>
        </div>
        """)


def render_comparison_card(row) -> None:
    from utils.matches import format_kickoff
    from utils.predictions import format_actual_score, format_predicted_score, format_winner

    home = row["home_team"]
    away = row["away_team"]
    round_name = row["round"]
    kickoff = format_kickoff(row["date_utc"])
    venue = row["venue"]
    predicted = format_predicted_score(row)
    actual = format_actual_score(row)

    if row["exact_score"]:
        badge_class = "wc-badge-exact"
        badge_label = "Exact score"
    elif row["result_match"]:
        badge_class = "wc-badge-miss"
        badge_label = f"Wrong off by {int(row['goal_error'])} goals"
    else:
        badge_class = "wc-badge-upcoming"
        badge_label = "Upcoming match"

    center_html = (
        f'<div class="wc-score">'
        f"<div>{predicted} | {actual}</div>"
        f'<div class="wc-score-pens">Predicted | Actual</div>'
        f"</div>"
    )
    meta_extra = f" · Predicted Winner: {format_winner(row)}"

    render_html(f"""
        <div class="wc-card">
            <span class="wc-badge {badge_class}">{badge_label}</span>
            <span style="margin-left:0.5rem;color:#666;font-size:0.85rem;">{round_name}</span>
            <div class="wc-match-row">
                {_team_cell(home)}
                {center_html}
                {_team_cell(away, away=True)}
            </div>
            <div class="wc-meta">{kickoff} · Stadium: {venue}{meta_extra}</div>
        </div>
        """)


def _render_probability_row(label: str, value: float, scale: float) -> None:
    st.caption(label)
    st.progress(min(value / scale, 1.0) if scale > 0 else 0.0, text=f"{value:.1f}%")


def render_monte_carlo_champion_stats(df) -> None:
    from utils.predictions import (
        monte_carlo_tier,
        monte_carlo_total_simulations,
        team_champion_narrative,
    )
    from utils.teams import all_teams_from_fixtures, is_slot_team

    if df.empty:
        st.info("Monte Carlo results are not available yet.")
        return

    tournament_teams = {t for t in all_teams_from_fixtures() if not is_slot_team(t)}
    contenders = df[df["team"].isin(tournament_teams) & (df["win_percent"] > 0)].copy()
    if contenders.empty:
        contenders = df[df["win_percent"] > 0].copy()

    total_sims = monte_carlo_total_simulations(df)
    favorite = contenders.iloc[0]
    best_podium = contenders.sort_values("podium_percent", ascending=False).iloc[0]
    title_race = int((contenders["win_percent"] >= 1).sum())

    st.subheader("🏆 Monte Carlo trophy simulator")
    st.markdown(
        f"We replayed the knockout bracket **{total_sims:,}** times using Elo-weighted outcomes. "
        "Below is how often each team finishes as champion, runner-up, or on the podium."
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Simulations run", f"{total_sims:,}")
    m2.metric("Title favourite", favorite["team"])
    m3.metric("Best podium profile", best_podium["team"])
    m4.metric("Teams with ≥1% title shot", title_race)

    st.markdown("#### Title race favourites")
    if len(contenders) < 3:
        for _, row in contenders.head(5).iterrows():
            st.markdown(
                f"- **{row['team']}** — {row['win_percent']:.1f}% title · "
                f"{row['podium_percent']:.1f}% podium"
            )
    else:
        top_three = contenders.head(3)
        podium_order = [
            (top_three.iloc[1], "🥈", "2nd favourite"),
            (top_three.iloc[0], "🥇", "Favourite"),
            (top_three.iloc[2], "🥉", "3rd favourite"),
        ]
        podium_cols = st.columns([1, 1.15, 1], gap="medium")
        for col, (row, medal, label) in zip(podium_cols, podium_order):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{medal} {label}**")
                    _show_team_flag(row["team"])
                    st.markdown(f"**{row['team']}**")
                    st.metric("Title chance", f"{row['win_percent']:.1f}%")
                    st.caption(
                        f"{int(row['champion']):,} simulated wins · "
                        f"{row['podium_percent']:.1f}% podium"
                    )

    st.subheader("Pick a team — read their fortune")
    team_options = contenders["team"].tolist()
    selected_team = st.selectbox("Choose a nation", options=team_options, label_visibility="collapsed")
    selected = contenders.loc[contenders["team"] == selected_team].iloc[0]
    tier = monte_carlo_tier(selected["win_percent"])
    narrative = team_champion_narrative(selected, total_sims)
    scale = max(selected["win_percent"], selected["podium_percent"], 0.1)
    runner_up_pct = selected["runner_up"] / total_sims * 100
    third_pct = selected["third_place"] / total_sims * 100

    with st.container(border=True):
        head_left, head_right = st.columns([1, 5], vertical_alignment="center")
        with head_left:
            _show_team_flag(selected_team, width=72)
        with head_right:
            st.markdown(f"### {selected_team}")
            st.caption(tier)
        st.write(narrative)
        _render_probability_row("Title", selected["win_percent"], scale)
        _render_probability_row("Podium", selected["podium_percent"], scale)
        _render_probability_row("Runner-up", runner_up_pct, scale)
        _render_probability_row("Third place", third_pct, scale)
        st.caption(
            f"Elo rating: **{int(selected['rating'])}** · "
            f"{int(selected['champion']):,} titles · "
            f"{int(selected['runner_up']):,} runners-up · "
            f"{int(selected['third_place']):,} third-place finishes"
        )

    st.subheader("Who belongs in each tier?")
    tiers = [
        ("Title heavyweights", contenders[contenders["win_percent"] >= 5]),
        ("Outside contenders", contenders[(contenders["win_percent"] >= 2) & (contenders["win_percent"] < 5)]),
        ("Dark horses", contenders[(contenders["win_percent"] >= 0.5) & (contenders["win_percent"] < 2)]),
        ("Long shots", contenders[(contenders["win_percent"] > 0) & (contenders["win_percent"] < 0.5)]),
    ]
    left_col, right_col = st.columns(2)
    for col, tier_group in [(left_col, tiers[:2]), (right_col, tiers[2:])]:
        with col:
            for title, subset in tier_group:
                st.markdown(f"**{title}**")
                if subset.empty:
                    st.caption("No teams in this band.")
                    continue
                for _, row in subset.head(6).iterrows():
                    st.markdown(
                        f"- **{row['team']}** — {row['win_percent']:.1f}% title · "
                        f"{row['podium_percent']:.1f}% podium"
                    )

    sleeper = contenders.sort_values(["podium_percent", "win_percent"], ascending=[False, True]).iloc[0]
    if sleeper["team"] != favorite["team"]:
        st.info(
            f"**Sleeper watch:** {sleeper['team']} punch above their title odds with "
            f"{sleeper['podium_percent']:.1f}% podium rate despite only "
            f"{sleeper['win_percent']:.1f}% to win it all."
        )


def render_monte_carlo_team_matchups(df) -> None:
    from utils.predictions import lookup_monte_carlo_matchup, monte_carlo_matchup_total_sims
    from utils.teams import all_teams_from_fixtures, is_slot_team

    if df.empty:
        st.info("Team matchups results are not available yet.")
        return

    total_sims = monte_carlo_matchup_total_sims(df)
    tournament_teams = sorted(
        {t for t in all_teams_from_fixtures() if not is_slot_team(t)}
    )
    teams_in_data = sorted(set(df["team_a"]) | set(df["team_b"]))
    team_options = sorted(set(tournament_teams) | set(teams_in_data))

    st.subheader("🤜🤛 Team matchups")
    st.markdown(
        f"Choose two nations to see the probability they **face each other** in the FIFA World Cup 2026. "
    )

    default_a = team_options.index("Portugal") if "Portugal" in team_options else 0
    default_b = (
        team_options.index("Argentina")
        if "Argentina" in team_options
        else min(1, len(team_options) - 1)
    )

    pick_left, pick_right = st.columns(2)
    with pick_left:
        team_a = st.selectbox(
            "Team A",
            options=team_options,
            index=default_a,
            key="matchup_team_a",
        )
    with pick_right:
        team_b_options = [t for t in team_options if t != team_a]
        team_b_index = (
            team_b_options.index("Argentina")
            if team_a != "Argentina" and "Argentina" in team_b_options
            else min(default_b, len(team_b_options) - 1)
        )
        team_b = st.selectbox(
            "Team B",
            options=team_b_options,
            index=team_b_index,
            key="matchup_team_b",
        )

    matchup_percent, matchup_count = lookup_monte_carlo_matchup(
        df, team_a, team_b, total_sims=total_sims,
    )

    with st.container(border=True):
        flag_left, vs_col, flag_right = st.columns([1, 0.4, 1], vertical_alignment="center")
        with flag_left:
            _show_team_flag(team_a, width=72)
            st.markdown(f"**{team_a}**")
        with vs_col:
            st.markdown("### vs")
        with flag_right:
            _show_team_flag(team_b, width=72)
            st.markdown(f"**{team_b}**")
        _render_probability_row("Probability they face each other in the FIFA World Cup 2026 is:", matchup_percent, 100.0)
        st.caption("This probability is based on the number of times these two teams have been simulated to face each other in the FIFA World Cup 2026.")


def render_group_standings(
    standings: dict,
    *,
    group_filter: list[str] | None = None,
) -> None:
    st.caption("Standings will be updated every 12 hours.")
    st.caption("P: Games played | W: Wins | D: Draws | L: Losses | GF: Goals for | GA: Goals against | GD: Goal difference | Pts: Points")

    groups = sorted(standings.keys())
    if group_filter:
        groups = [group for group in groups if group in group_filter]

    if not groups:
        st.info("No standings available for the selected groups.")
        return

    rank_column = st.column_config.TextColumn("#", width="small")
    team_column = st.column_config.TextColumn("Team", width="medium")
    stat_column = st.column_config.NumberColumn(width="small", alignment="left")

    for group in groups:
        table = standings[group].head(TEAMS_PER_GROUP).reset_index(drop=True).copy()
        table = table.sort_values(by=["Pts", "GD", "GF"], ascending=[False, False, False])
        table["#"] = table["#"].astype(str)
        st.markdown(f"**Group {group}**")
        st.dataframe(
            table,
            width='stretch',
            hide_index=True,
            height=STANDINGS_TABLE_HEIGHT,
            column_config={
                "#": rank_column,
                "Team": team_column,
                "P": stat_column,
                "W": stat_column,
                "D": stat_column,
                "L": stat_column,
                "GF": stat_column,
                "GA": stat_column,
                "GD": stat_column,
                "Pts": stat_column,
            },
        )

_SQUAD_POSITION_GROUPS = (
    ("GK", "🧤 Goalkeepers", "#b45309"),
    ("DF", "🛡️ Defenders", "#1d4ed8"),
    ("MF", "⚡ Midfielders", "#15803d"),
    ("FW", "🎯 Forwards", "#b91c1c"),
)

def _squad_field(value, label: str) -> str | None:
    import pandas as pd

    if pd.isna(value) or not str(value).strip():
        return None
    if label == "Height":
        try:
            return f"{label}: {int(float(value))} cm"
        except (TypeError, ValueError):
            return f"{label}: {value}"
    return f"{label}: {value}"


def _render_player_card(row, *, accent_color: str) -> None:
    name = html.escape(str(row.get("player_name") or "Unknown player"))
    shirt = row.get("name_on_shirt")
    meta_lines = [
        html.escape(line)
        for line in (
            _squad_field(row.get("club"), "Club"),
            _squad_field(row.get("height"), "Height"),
            _squad_field(row.get("dob"), "Born"),
        )
        if line
    ]
    shirt_html = ""
    if (
        shirt is not None
        and str(shirt).strip()
    ):
        shirt_html = f'<div class="wc-player-shirt">👕 Shirt: {html.escape(str(shirt))}</div>'

    meta_html = "<br>".join(meta_lines) if meta_lines else "—"
    render_html(f"""
        <div class="wc-player-card" style="--wc-pos-color: {accent_color};">
            <div class="wc-player-name">{name}</div>
            {shirt_html}
            <div class="wc-player-meta">{meta_html}</div>
        </div>
        """)


def _render_player_group(group, *, label: str, accent_color: str, cols_per_row: int = 3) -> None:
    render_html(
        f'<div class="wc-squad-pos-title" style="--wc-pos-color: {accent_color};">{label}</div>'
    )
    players = [row for _, row in group.iterrows()]
    for start in range(0, len(players), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, row in zip(cols, players[start:start + cols_per_row]):
            with col:
                _render_player_card(row, accent_color=accent_color)


def _render_coach_card(coach) -> None:
    import pandas as pd

    from utils.squads import coach_display_name
    from utils.teams import flag_static_url

    name = html.escape(coach_display_name(coach))
    nationality = coach.get("nationality")
    nationality_html = ""
    if pd.notna(nationality) and str(nationality).strip():
        nat = str(nationality).strip()
        nationality_html = f"Nationality: {html.escape(nat)}"
    render_html(f"""
        <div class="wc-coach-card">
            <div class="wc-coach-label">📋 Head coach</div>
            <div class="wc-coach-name">{name}</div>
            <div class="wc-coach-meta">
                {nationality_html}
            </div>
        </div>
        """)


def render_squad_table(team_name: str) -> None:
    from utils.squads import split_squad_players_coach

    try:
        squad = get_squad(team_name)
    except KeyError:
        st.warning(f"Squad data for **{team_name}** is not available.")
        return

    players, coach = split_squad_players_coach(squad)

    head_left, head_right = st.columns([1, 5], vertical_alignment="center")
    with head_left:
        _show_team_flag(team_name, width=72)
    with head_right:
        st.markdown(f"### {team_name}")
        coach_note = " · 1 Head Coach" if coach is not None else ""
        st.caption(f"{len(players)} players{coach_note}")

    if coach is not None:
        _render_coach_card(coach)

    if players.empty:
        st.info("No player rows found for this squad.")
        return

    counts = players["position"].value_counts()
    metric_cols = st.columns(4)
    for col, (code, label, _) in zip(metric_cols, _SQUAD_POSITION_GROUPS):
        col.metric(label.split(" ", 1)[1], int(counts.get(code, 0)))

    for code, label, color in _SQUAD_POSITION_GROUPS:
        group = players[players["position"] == code]
        if group.empty:
            continue
        _render_player_group(group, label=label, accent_color=color)