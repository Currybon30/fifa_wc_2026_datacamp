import streamlit as st

from utils.ui import inject_base_styles, render_copyright_footer, render_html

st.set_page_config(page_title="Data", page_icon="📊", layout="wide")

inject_base_styles()


st.title("📊 Data Sources")
st.caption("Fixtures, knockout slots, and competition datasets.")

st.divider()

st.write("To access the datasets, please visit my [Kaggle World Cup 2026 Data](https://www.kaggle.com/datasets/tuongnguyenpham/fifa-wc26-data).")


st.divider()

# Create a contact info
st.write("If you have any questions, suggestions, or feedback to improve this system for this special event, please don't hesitate to contact me at [tuongnguyen2004dng@gmail.com](mailto:tuongnguyen2004dng@gmail.com).")

render_copyright_footer()
