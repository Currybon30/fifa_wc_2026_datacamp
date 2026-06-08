import streamlit as st

from utils.ui import inject_base_styles, render_copyright_footer, render_html

st.set_page_config(page_title="Data", page_icon="📊", layout="wide")

inject_base_styles()


st.warning("The website is still under development. Some features are not available or incomplete. We will keep updating it as the tournament progresses. Thank you for your patience.")

st.title("📊 Data Sources")
st.caption("Fixtures, knockout slots, and competition datasets.")

st.divider()

st.write("To access the datasets, please visit my [Kaggle World Cup 2026 Data](https://www.kaggle.com/datasets/tuongnguyenpham/fifa-wc26-data).")

st.write("To view my full project, please visit my [GitHub repository](https://github.com/Currybon30/fifa_wc_2026_datacamp).")

st.divider()

# Create a contact info
st.write("If you have any questions, suggestions, or feedback to improve this system, please don't hesitate to contact me at [tuongnguyen2004dng@gmail.com](mailto:tuongnguyen2004dng@gmail.com).")

render_copyright_footer()
