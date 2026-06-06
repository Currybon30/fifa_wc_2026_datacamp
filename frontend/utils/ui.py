"""Shared Streamlit UI helpers."""

from datetime import datetime

import streamlit as st

from utils.standings import STANDINGS_TABLE_HEIGHT, TEAMS_PER_GROUP


def inject_base_styles() -> None:
    st.markdown(
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
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_copyright_footer() -> None:
    year = datetime.now().year
    if year == 2026:
        st.markdown(
            f"""
            <div class="wc-footer">
                © 2026 Tuong Nguyen Pham - FIFA World Cup 2026 Prediction System. All rights reserved.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="wc-footer">
                © 2026 - {year} Tuong Nguyen Pham - FIFA World Cup 2026 Prediction System. All rights reserved.
            </div>
            """,
            unsafe_allow_html=True,
        )


def _team_cell(team_name: str, *, away: bool = False) -> str:
    from utils.teams import flag_static_url

    url = flag_static_url(team_name)
    align_class = "wc-team-away" if away else "wc-team-home"
    flag_html = f'<img src="{url}" class="wc-flag" alt="" />'
    if away:
        return f'<div class="wc-team {align_class}"><span style="color: black;">{team_name}</span>{flag_html}</div>'
    return f'<div class="wc-team {align_class}">{flag_html}<span style="color: black;">{team_name}</span></div>'


def render_match_card_api(fixture: dict, *, live: bool = False) -> None:
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

        st.markdown(
            f"""
            <div class="{card_class}">
                <span class="wc-badge {badge_class}">{status_label}</span>
                <span style="margin-left:0.5rem;color:#666;font-size:0.85rem;">{round_name}</span>
                <div class="wc-match-row">
                    {_team_cell(home)}
                    {score_html}
                    {_team_cell(away, away=True)}
                </div>
                <div class="wc-meta">{format_kickoff(fixture["fixture"]["date"])} · {location}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        from utils.matches import (
            fd_match_away_team,
            fd_match_home_team,
            fd_match_round_name,
            fd_match_score_lines,
            fd_status_badge,
            format_kickoff,
        )

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

        st.markdown(
            f"""
            <div class="wc-card">
                <span class="wc-badge {badge_class}">{status_label}</span>
                <span style="margin-left:0.5rem;color:#666;font-size:0.85rem;">{round_name}</span>
                <div class="wc-match-row">
                    {_team_cell(home)}
                    {score_html}
                    {_team_cell(away, away=True)}
                </div>
                <div class="wc-meta">{format_kickoff(fixture["utcDate"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


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

    st.markdown(
        f"""
        <div class="{card_class}">
            <span class="wc-badge {badge_class}">{status_badge(status)}</span>
            <span style="margin-left:0.5rem;color:#666;font-size:0.85rem;">{row["round"]}</span>
            <div class="wc-match-row">
                {_team_cell(row["home_team"])}
                <div class="wc-score">vs</div>
                {_team_cell(row["away_team"], away=True)}
            </div>
            <div class="wc-meta">{format_kickoff(row["date_utc"])} · {row["venue"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    st.markdown(
        f"""
        <div class="wc-card">
            <span class="wc-badge wc-badge-upcoming">Predicted</span>
            <span style="margin-left:0.5rem;color:#666;font-size:0.85rem;">{round_name}</span>
            <div class="wc-match-row">
                {_team_cell(home)}
                {center_html}
                {_team_cell(away, away=True)}
            </div>
            <div class="wc-meta">{kickoff} · {venue}{meta_extra}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
        badge_class = "wc-badge-upcoming"
        badge_label = "Result match"
    else:
        badge_class = "wc-badge-miss"
        badge_label = f"Off by {int(row['goal_error'])} goals"

    center_html = (
        f'<div class="wc-score">'
        f"<div>{predicted} → {actual}</div>"
        f'<div class="wc-score-pens">Predicted → Actual</div>'
        f"</div>"
    )
    meta_extra = f" · Predicted winner: {format_winner(row)}"

    st.markdown(
        f"""
        <div class="wc-card">
            <span class="wc-badge {badge_class}">{badge_label}</span>
            <span style="margin-left:0.5rem;color:#666;font-size:0.85rem;">{round_name}</span>
            <div class="wc-match-row">
                {_team_cell(home)}
                {center_html}
                {_team_cell(away, away=True)}
            </div>
            <div class="wc-meta">{kickoff} · {venue}{meta_extra}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
