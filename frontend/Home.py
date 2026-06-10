import streamlit as st

from utils.matches import format_date_local, format_kickoff, load_local_fixtures, split_local_fixtures
from utils.usertimezone import render_country_timezone_selector
from utils.ui import inject_base_styles, render_copyright_footer, render_html
from utils.countdown import countdown_timer, seconds_until_world_cup_start, format_world_cup_countdown
from config.logging import setup_logging

# Initialize logging
setup_logging()

st.set_page_config(
    page_title="FIFA World Cup 2026",
    page_icon="⚽",
    layout="wide",
)

wc_countdown_remaining = seconds_until_world_cup_start()

@st.dialog(title=" ")
def wc_countdown_dialog():
    st.title("⏳ FIFA World Cup 2026 Countdown")
    st.metric(
        "The FIFA World Cup 2026 will start in:",
        format_world_cup_countdown(wc_countdown_remaining),
    )
    st.caption("Please open the sidebar for more options.")
    
if wc_countdown_remaining > 0:
    wc_countdown_dialog()

countdown_timer() # Sidebar

with st.sidebar:
    render_country_timezone_selector()

inject_base_styles()

from utils.teams import is_slot_team

fixtures = load_local_fixtures()
group_fixtures = fixtures[fixtures["stage"] == "group"]
knockout_fixtures = fixtures[fixtures["stage"] == "knockout"]
groups = group_fixtures["group"].nunique()
teams = sorted(
    t for t in set(group_fixtures["home_team"]) | set(group_fixtures["away_team"])
    if not is_slot_team(t)
)
first_match = group_fixtures.iloc[0]
last_match = fixtures.iloc[-1]

render_html("""
    <div class="wc-hero">
        <div class="wc-hero-content">
            <h1>⚽ FIFA World Cup 2026</h1>
            <p>USA · Canada · Mexico — Follow live action, upcoming fixtures, and tournament insights.</p>
        </div>
        <img
            src="app/static/tournaments_fifa-world-cup-2026--white_128x128.football-logos.cc.png"
            class="wc-hero-logo"
            alt="FIFA World Cup 2026 logo"
        />
    </div>
    """)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Group stage matches", len(group_fixtures))
col2.metric("Knockout matches", len(knockout_fixtures))
col3.metric("Groups", groups)
col4.metric("Teams", len(teams))

st.divider()

st.subheader("Explore the tournament")

nav1, nav2, nav3, nav4 = st.columns(4)

with nav1:
    render_html("""
        <div class="wc-nav-card">
            <h3>⚽ World Cup 2026</h3>
            <p>Live matches, upcoming fixtures, and full-time results from the tournament.</p>
        </div>
        """)
    st.page_link("pages/1_⚽_World_Cup_2026.py", label="Open matches hub →")

with nav2:
    render_html("""
        <div class="wc-nav-card">
            <h3>🔮 Predictions</h3>
            <p>Submit and review score predictions for every group and knockout match.</p>
        </div>
        """)
    st.page_link("pages/2_🔮_Predictions.py", label="Go to predictions →")

with nav3:
    render_html("""
        <div class="wc-nav-card">
            <h3>📈 Analysis</h3>
            <p>Explore team form, Elo ratings, and historical World Cup statistics.</p>
        </div>
        """)
    st.page_link("pages/3_📈_Analysis.py", label="View analysis →")

with nav4:
    render_html("""
        <div class="wc-nav-card">
            <h3>📊 Data Sources</h3>
            <p>Browse fixtures, knockout slots, and competition datasets.</p>
        </div>
        """)
    st.page_link("pages/4_📊_Data_Sources.py", label="Browse data sources →")

st.divider()

st.subheader("Next upcoming matches")

_, upcoming_fixtures, _ = split_local_fixtures(fixtures)
preview = upcoming_fixtures.head(5)[["round", "home_team", "away_team", "date_utc", "venue"]].copy()
preview["date_utc"] = preview["date_utc"].map(format_kickoff)
preview.columns = ["Round", "Home", "Away", "Kickoff", "Venue"]
st.dataframe(preview, width='stretch', hide_index=True)

st.caption(
    f"Showing the next {len(preview)} upcoming matches. "
    f"Tournament runs {format_date_local(first_match['date_utc'])} – "
    f"{format_date_local(last_match['date_utc'])} (local dates)."
)

render_copyright_footer()
