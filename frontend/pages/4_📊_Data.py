import streamlit as st

from utils.ui import inject_base_styles, render_copyright_footer

st.set_page_config(page_title="Data", page_icon="📊", layout="wide")

inject_base_styles()

st.title("📊 Data")
st.caption("Fixtures, knockout slots, and competition datasets.")

render_copyright_footer()
