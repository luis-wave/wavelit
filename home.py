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

        report_page = st.Page("sigma_dashboards/reports.py", title="Queue")

        dods_dashboards_page = st.Page(
            "sigma_dashboards/dods_dashboards.py", title="DoDS Dashboards"
        )

        admin_page = st.Page(
            "sigma_dashboards/wavelit_admin.py", title="Teammate Availability"
        )

        admin_page = st.Page("sigma_dashboards/wavelit_admin.py", title="Wavelit Admin")

        eeg_page = st.Page(
            "streamlit_apps/eeg.py", title="EEG", icon="🧠", url_path="/eeg"
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

        neurosynchrony_page = st.Page(
            "streamlit_apps/neurosynchrony.py",
            title="MeRT2",
            icon="📨",
            url_path="/mert_reports",
        )

        nav = st.navigation(
            {
                "Sigma Dashboards": [
                    report_page,
                    protocol_page,
                    dods_dashboards_page,
                    admin_page,
                ],
                "Tools": [eeg_page, ecg_page, neurosynchrony_page],
                "Research & Development": [epoch_page, ngboost_page],
            }
        )

        nav.run()
