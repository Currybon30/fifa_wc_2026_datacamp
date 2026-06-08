import streamlit as st

from utils.matches import (
    fetch_api_fixtures,
    fetch_live_fixtures,
    filter_upcoming_local_fixtures,
    format_refresh_countdown,
    get_api_football_key,
    get_football_data_key,
    load_local_fixtures,
    seconds_until_live_api_refresh,
    split_api_fixtures,
    split_local_fixtures,
)
from utils.standings import get_football_data_key, get_group_standings
from utils.ui import inject_base_styles, render_copyright_footer, render_group_standings, render_match_card_api, render_match_card_local

st.set_page_config(page_title="World Cup 2026", page_icon="⚽", layout="wide")

inject_base_styles()


st.warning("The website is still under development. Some features are not available or incomplete. We will keep updating it as the tournament progresses. Thank you for your patience.")

st.title("⚽ World Cup 2026")
st.caption("Live scores, fixtures, and group standings.")

api_football_key = get_api_football_key()
football_data_key = get_football_data_key()
using_api = api_football_key is not None and football_data_key is not None

with st.sidebar:
    group_filter = st.multiselect(
        "Filter by group",
        options=sorted(load_local_fixtures()["group"].dropna().unique()),
        default=[],
    )
    limit = st.slider("Matches to show", min_value=5, max_value=104, value=20, step=5)

live_fixtures: list = []
completed_fixtures: list = []
data_error: str | None = None

df = load_local_fixtures()
if group_filter:
    df = df[(df["stage"] != "group") | df["group"].isin(group_filter)]
live_df, upcoming_df, completed_df = split_local_fixtures(df)

if using_api:
    try:
        non_live_fixtures = fetch_api_fixtures(football_data_key)
        live_fixtures = fetch_live_fixtures(api_football_key)
        _, completed_fixtures = split_api_fixtures(non_live_fixtures)
    except Exception as exc:
        data_error = str(exc)
        using_api = False


@st.fragment(run_every=1)
def _render_live_refresh_countdown() -> None:
    remaining = seconds_until_live_api_refresh()
    if remaining <= 0:
        st.caption("Refreshing live scores…")
        st.rerun()
        return
    st.metric("Next live score refresh", format_refresh_countdown(remaining))


with st.sidebar:
    st.divider()
    if using_api and not data_error:
        _render_live_refresh_countdown()
    elif not using_api:
        st.caption("Configure API keys to enable live score refresh.")

display_upcoming_df = filter_upcoming_local_fixtures(
    upcoming_df,
    live_df=live_df,
    live_fixtures=live_fixtures if using_api else None,
    completed_df=completed_df,
    completed_fixtures=completed_fixtures if using_api else None,
)

standings: dict = {}
standings_error: str | None = None

football_data_key = get_football_data_key()
if football_data_key:
    try:
        standings = get_group_standings(football_data_key)
    except Exception as exc:
        standings_error = str(exc)

tab_live, tab_upcoming, tab_completed, tab_standings = st.tabs(
    [
        f"🔴 Live ({len(live_fixtures) if using_api else len(live_df)})",
        f"📅 Upcoming ({len(display_upcoming_df)})",
        f"✅ Completed ({len(completed_fixtures) if using_api else len(completed_df)})",
        "📋 Standings",
    ]
)

if data_error:
    st.error(f"❗Could not reach API-Sports API. Showing non-live fixtures without live scores instead. Sorry for the inconvenience.")

with tab_live:
    st.warning(f"⚠️ The system is still under development, all of the live matches below are not the FIFA World Cup 2026 matches. We will update once the tournament starts.")
    st.info(f"Due to the limitation of the API-Sports free tier, we can only update the live scores every 20 minutes. Thank you for your understanding.")
    if using_api:
        if live_fixtures:
            for fixture in live_fixtures:
                render_match_card_api(fixture, live=True)
        else:
            st.info("No World Cup matches are live right now. Check the Upcoming tab for the next kickoffs.")
    elif len(live_df):
        for _, row in live_df.iterrows():
            render_match_card_local(row, live=True)
    else:
        st.info("No matches are live right now. The tournament kicks off soon — see Upcoming for the schedule.")

with tab_upcoming:
    shown = display_upcoming_df.head(limit)
    if len(shown):
        for _, row in shown.iterrows():
            render_match_card_local(row)
    else:
        st.success("No upcoming fixtures in the local schedule.")

with tab_completed:
    if using_api:
        shown = completed_fixtures[:limit]
        if shown:
            for fixture in shown:
                render_match_card_api(fixture)
        else:
            st.info("No completed matches yet — the tournament has not started.")
    else:
        shown = completed_df.head(limit)
        if len(shown):
            for _, row in shown.iterrows():
                render_match_card_local(row, finished=True)
        else:
            st.info("No completed matches yet — the tournament has not started.")

with tab_standings:
    if not football_data_key:
        st.error(
            "Football-data.org API key is not configured. Standings will be available once it is set."
        )
    elif standings_error:
        st.warning(f"Could not load standings from football-data.org ({standings_error}).")
    elif not standings:
        st.info("No standings data is available from football-data.org yet.")
    else:
        render_group_standings(standings, group_filter=group_filter or None)

render_copyright_footer()
