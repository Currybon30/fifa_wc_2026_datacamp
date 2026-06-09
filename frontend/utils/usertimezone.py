"""Viewer timezone selection — UTC default, optional country conversion."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import streamlit as st

from utils.teams import all_teams_from_fixtures, is_slot_team

UTC_OPTION_LABEL = "Universal Time Coordinated"

# Primary IANA zone per nation (World Cup teams + common viewer countries).
COUNTRY_TIMEZONES: dict[str, str] = {
    UTC_OPTION_LABEL: "UTC",
    "Algeria": "Africa/Algiers",
    "Argentina": "America/Argentina/Buenos_Aires",
    "Australia": "Australia/Sydney",
    "Austria": "Europe/Vienna",
    "Belgium": "Europe/Brussels",
    "Bosnia and Herzegovina": "Europe/Sarajevo",
    "Brazil": "America/Sao_Paulo",
    "Cabo Verde": "Atlantic/Cape_Verde",
    "Canada": "America/Toronto",
    "Colombia": "America/Bogota",
    "Costa Rica": "America/Costa_Rica",
    "Croatia": "Europe/Zagreb",
    "Curaçao": "America/Curacao",
    "Czechia": "Europe/Prague",
    "DR Congo": "Africa/Kinshasa",
    "Ecuador": "America/Guayaquil",
    "Egypt": "Africa/Cairo",
    "England": "Europe/London",
    "France": "Europe/Paris",
    "Germany": "Europe/Berlin",
    "Ghana": "Africa/Accra",
    "Haiti": "America/Port-au-Prince",
    "Iran": "Asia/Tehran",
    "Iraq": "Asia/Baghdad",
    "Japan": "Asia/Tokyo",
    "Jordan": "Asia/Amman",
    "Mexico": "America/Mexico_City",
    "Morocco": "Africa/Casablanca",
    "Netherlands": "Europe/Amsterdam",
    "New Zealand": "Pacific/Auckland",
    "Nigeria": "Africa/Lagos",
    "Norway": "Europe/Oslo",
    "Panama": "America/Panama",
    "Paraguay": "America/Asuncion",
    "Portugal": "Europe/Lisbon",
    "Qatar": "Asia/Qatar",
    "Saudi Arabia": "Asia/Riyadh",
    "Senegal": "Africa/Dakar",
    "South Africa": "Africa/Johannesburg",
    "South Korea": "Asia/Seoul",
    "Spain": "Europe/Madrid",
    "Sweden": "Europe/Stockholm",
    "Switzerland": "Europe/Zurich",
    "Tunisia": "Africa/Tunis",
    "Turkey": "Europe/Istanbul",
    "USA": "America/New_York",
    "Uruguay": "America/Montevideo",
    "Uzbekistan": "Asia/Tashkent",
    "India": "Asia/Kolkata",
    "Singapore": "Asia/Singapore",
    "Vietnam": "Asia/Ho_Chi_Minh",
}


def _country_options() -> list[str]:
    tournament_teams = [
        t for t in all_teams_from_fixtures() if not is_slot_team(t)
    ]
    extras = ["India", "Singapore", "Vietnam"]
    countries = {UTC_OPTION_LABEL}
    for team in tournament_teams:
        countries.add(team)
    countries.update(extras)
    ordered = [UTC_OPTION_LABEL] + sorted(c for c in countries if c != UTC_OPTION_LABEL)
    return ordered


def get_user_timezone() -> ZoneInfo:
    """Return the viewer zone from session state (UTC by default)."""
    iana = st.session_state.get("viewer_timezone_iana", "UTC")
    try:
        return ZoneInfo(iana)
    except Exception:
        return ZoneInfo("UTC")


def render_country_timezone_selector() -> None:
    """Sidebar: UTC kickoffs by default, optional convert to a country zone."""
    options = _country_options()
    labels_to_iana = {
        country: COUNTRY_TIMEZONES.get(country, "UTC") for country in options
    }

    i = st.session_state.get("viewer_country_index", 0)
    selected = st.selectbox(
        "Select your country to convert to your local time",
        options=options,
        index=i,
        key="viewer_country_label",
    )
    st.session_state["viewer_timezone_iana"] = labels_to_iana[selected]
    st.session_state["viewer_country_index"] = options.index(selected)

    if selected == UTC_OPTION_LABEL:
        st.caption("Kickoffs are shown in **UTC**.")
    else:
        st.caption(
            f"UTC kickoffs converted to **{labels_to_iana[selected]}** timezone."
        )
