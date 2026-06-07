import streamlit as st

from utils.ui import inject_base_styles, render_copyright_footer

st.set_page_config(page_title="Data", page_icon="📊", layout="wide")

inject_base_styles()

st.title("📊 Data Sources")
st.caption("Fixtures, knockout slots, and competition datasets.")

st.markdown("""
    <hr>
    """, unsafe_allow_html=True)

st.write("To access the datasets, please visit my [Kaggle World Cup 2026 Data](https://www.kaggle.com/datasets/tuongnguyenpham/fifa-wc26-data).")

st.write("To view my full project, please visit my [GitHub repository](https://github.com/Currybon30/fifa_wc_2026_datacamp).")

st.markdown("""
    <hr>
    """, unsafe_allow_html=True)

# Create a contact info
st.write("If you have any questions, suggestions, or feedback to improve this system, please don't hesitate to contact me at [tuongnguyen2004dng@gmail.com](mailto:tuongnguyen2004dng@gmail.com).")

render_copyright_footer()
