import streamlit as st
from datetime import datetime, timezone

KICKOFF_UTC = datetime(2026, 6, 11, 19, 0, 0, tzinfo=timezone.utc)


def format_world_cup_countdown(seconds: float | int) -> str:
    total = max(0, int(seconds))
    days, rem = divmod(total, 86_400)
    hours, rem = divmod(rem, 3_600)
    minutes, secs = divmod(rem, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs:
        parts.append(f"{secs:02d}s")
    return " ".join(parts)


def seconds_until_world_cup_start():
    """
    Calculate the number of seconds until the FIFA World Cup 2026 starts.
    """
    return (KICKOFF_UTC - datetime.now(timezone.utc)).total_seconds()

@st.fragment(run_every=1)
def _render_world_cup_countdown() -> None:
    remaining = seconds_until_world_cup_start()
    if remaining <= 0:
        st.title("🎉 FIFA World Cup 2026 is kicking off!")
        return
    st.title("⏳ FIFA World Cup 2026 Countdown")
    st.metric(
        "The FIFA World Cup 2026 will start in:",
        format_world_cup_countdown(remaining),
    )


@st.fragment(run_every=1)
def _render_world_cup_countdown_dialog_body() -> None:
    remaining = seconds_until_world_cup_start()
    if remaining <= 0:
        st.title("🎉 FIFA World Cup 2026 is kicking off!")
        return
    st.title("⏳ FIFA World Cup 2026 Countdown")
    st.metric(
        "The FIFA World Cup 2026 will start in:",
        format_world_cup_countdown(remaining),
    )
    st.caption("Please open the sidebar for more options.")


@st.dialog(title=" ")
def open_world_cup_countdown_dialog() -> None:
    _render_world_cup_countdown_dialog_body()


def countdown_timer():
    """Display a countdown timer to the FIFA World Cup 2026."""
    with st.sidebar:
        _render_world_cup_countdown()