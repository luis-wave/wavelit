

import asyncio

import streamlit as st

from access_control import access_eeg_data, get_version_from_pyproject
from streamlit_dashboards import ecg_visualization_dashboard

asyncio.run(access_eeg_data())

ecg_visualization_dashboard()


# Footer section
version = get_version_from_pyproject()
footer_html = f"""
    <div style='position: fixed; bottom: 0; left: 0; padding: 10px;'>
        <span>Version: {version}</span>
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
