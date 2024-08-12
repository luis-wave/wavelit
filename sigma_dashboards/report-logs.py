import asyncio

import streamlit as st
import streamlit.components.v1 as components

from access_control import access_eeg_data, get_version_from_pyproject
from streamlit_dashboards import (ecg_visualization_dashboard,
                                  eeg_epoch_visualization_dashboard,
                                  eeg_visualization_dashboard)

# Streamlit app setup
# st.set_page_config(page_title="Neuroref Report Dashboard", layout="wide")


# Title
st.title("Report Log Dashboard")

url = "https://app.sigmacomputing.com/embed/1-QcWTFngW18VskMHuiDbeA"

html = f'<iframe src="{url}" frameborder="0" width="100%" height="900px"></iframe>'


components.html(html, height=1000, scrolling=False)


# Footer section
version = get_version_from_pyproject()
footer_html = f"""
    <div style='position: fixed; bottom: 0; left: 0; padding: 10px;'>
        <span>Version: {version}</span>
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
