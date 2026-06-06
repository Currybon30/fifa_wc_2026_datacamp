import streamlit as st

from utils.ui import inject_base_styles, render_copyright_footer

st.set_page_config(page_title="Analysis", page_icon="📈", layout="wide")

inject_base_styles()

st.title("📈 Analysis")
st.caption("Team form, Elo ratings, and historical World Cup statistics.")

render_copyright_footer()
