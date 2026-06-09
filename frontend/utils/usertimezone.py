import streamlit as st
import requests

def get_user_timezone():
    try:
        response = requests.get("http://ip-api.com/json", verify=False)
        data = response.json()
        return data["timezone"]
    except Exception as e:
        st.error(f"Error getting user timezone: {e}")
        return None
