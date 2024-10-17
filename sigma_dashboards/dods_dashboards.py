import asyncio
import os

import streamlit as st
import streamlit.components.v1 as components

from access_control import access_eeg_data, get_version_from_pyproject
from streamlit_dashboards import (ecg_visualization_dashboard,
                                  eeg_epoch_visualization_dashboard,
                                  eeg_visualization_dashboard)

SIGMA_REPORT_LOGS_URL = os.getenv("SIGMA_REPORT_LOGS_URL")
SIGMA_DODS_KPI_URL = os.getenv("SIGMA_DODS_KPI_URL")

# Title
st.title("Report Log Dashboard")


html = f'<iframe src="{SIGMA_REPORT_LOGS_URL}" frameborder="0" width="100%" height="900px"></iframe>'


components.html(html, height=1000, scrolling=False)


st.title("DoDS KPI  Dashboard")


html = f'<iframe src="{SIGMA_DODS_KPI_URL}" frameborder="0" width="100%" height="900px"></iframe>'


components.html(html, height=1000, scrolling=False)


# Footer section
version = get_version_from_pyproject()
footer_html = f"""
    <div style='position: fixed; bottom: 0; left: 0; padding: 10px;'>
        <span>Version: {version}</span>
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
