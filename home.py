import os

import streamlit as st
import streamlit.components.v1 as components

from access_control import authorize_user_access

st.set_page_config(page_title="Home Page", layout="wide")

if __name__ == "__main__":
    user = None

    user = authorize_user_access()

    if user:
        # Streamlit app setup

        protocol_page = st.Page("sigma_dashboards/protocols.py", title="Protocols")

        report_page = st.Page("sigma_dashboards/reports.py", title="Reports")

        eeg_page = st.Page(
            "streamlit_apps/🧠 eeg.py", title="EEG", icon="🧠", url_path="/eeg"
        )

        ecg_page = st.Page(
            "streamlit_apps/❤️ ecg.py", title="ECG", icon="❤️", url_path="/ecg"
        )

        nav = st.navigation(
            {
                "Sigma Dashboards": [protocol_page, report_page],
                "Tools": [eeg_page, ecg_page],
            }
        )

        nav.run()
