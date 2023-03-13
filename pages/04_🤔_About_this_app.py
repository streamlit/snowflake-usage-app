import streamlit as st

st.set_page_config(page_title="Usage Insights app - About", page_icon="🤔", layout="centered")

from app_utils import gui

gui.icon("🤔")
st.title("About this app")

st.write(
    """
### How does this app work?

- Using [Streamlit](https://www.streamlit.io) and the [Snowflake Python
  connector](https://github.com/snowflakedb/snowflake-connector-python).
- Check out our public repository 🐙
  [snowflake-usage-app](https://github.com/streamlit/snowflake-usage-app) to
  learn more about it!

### Questions? Comments?

Please ask in the [Streamlit community](https://discuss.streamlit.io).
"""
)
