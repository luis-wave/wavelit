import asyncio

import streamlit as st

from access_control import access_eeg_data, get_version_from_pyproject
from streamlit_dashboards import eeg_visualization_dashboard

if "eegid" in st.session_state:
    asyncio.run(access_eeg_data(st.session_state.eegid))
    eeg_visualization_dashboard()

else:
    eeg_id = st.text_input("Enter EEG ID")
    if st.button("Download EEG Data"):
        st.session_state["eegid"] = eeg_id
        asyncio.run(access_eeg_data(st.session_state.eegid))
        eeg_visualization_dashboard()

# Footer section
version = get_version_from_pyproject()
footer_html = f"""
    <div style='position: fixed; bottom: 0; left: 0; padding: 10px;'>
        <span>Version: {version}</span>
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
