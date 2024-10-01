import os

import streamlit as st
import streamlit.components.v1 as components

from access_control import authorize_user_access

st.set_page_config(page_title="Home Page", layout="wide")

if __name__ == "__main__":
    user = None

    user = authorize_user_access()

    st.session_state["user"] = user

    if user:
        # Streamlit app setup

        protocol_page = st.Page("sigma_dashboards/protocols.py", title="Protocols")

        report_page = st.Page("sigma_dashboards/reports.py", title="Reports")

        report_log_page = st.Page(
            "sigma_dashboards/report-logs.py", title="Report Logs"
        )

        eeg_page = st.Page(
            "streamlit_apps/🧠 eeg.py", title="EEG", icon="🧠", url_path="/eeg"
        )

        ecg_page = st.Page(
            "streamlit_apps/❤️ ecg.py", title="ECG", icon="❤️", url_path="/ecg"
        )

        epoch_page = st.Page(
            "streamlit_apps/🌊 epochs.py", title="Epochs", icon="🌊", url_path="/epochs"
        )

        ngboost_page = st.Page(
            "streamlit_apps/ngboost.py",
            title="NGBoost Protocol",
            icon="🔬",
            url_path="/ngboost",
        )

        surveys_page = st.Page(
            "streamlit_apps/surveys.py",
            title="Typeform",
            icon="📨",
            url_path="/typeform",
        )

        reports_page = st.Page(
            "streamlit_apps/neurosynchrony.py",
            title="MeRT 2 Reports",
            icon="📨",
            url_path="/mert_reports",
        )

        protocols_page = st.Page(
            "streamlit_apps/protocols.py",
            title="MeRT 2 Protocols",
            icon="🧘",
            url_path="/mert_protocols",
        )

        nav = st.navigation(
            {
                "Sigma Dashboards": [report_page, protocol_page, report_log_page],
                "Tools": [eeg_page, ecg_page, epoch_page, reports_page, protocols_page],
                "Research & Development": [ngboost_page],
                "Surveys": [surveys_page],
            }
        )

        nav.run()
