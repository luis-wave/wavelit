import asyncio
import os

import streamlit as st
import streamlit.components.v1 as components

from access_control import access_eeg_data, get_version_from_pyproject
from streamlit_dashboards import (ecg_visualization_dashboard,
                                  eeg_epoch_visualization_dashboard,
                                  eeg_visualization_dashboard)

SIGMA_REPORT_URL = os.getenv("SIGMA_REPORT_URL")

# Check if query parameters exist and set eeg_id if available
query_params = st.query_params.to_dict()
if "eegId" in query_params:
    eeg_id = query_params["eegId"]
    st.write(eeg_id)
else:
    eeg_id = None

if "ecg" in query_params:
    show_ecg = True
else:
    show_ecg = False

if "eeg" in query_params:
    show_eeg = True
else:
    show_eeg = False

# These set of query parameters are relevant for Neurosynchrony report and protocol review.
if "eegid" in query_params:
    eegid = query_params["eegid"]
else:
    eegid = None

if "pid" in query_params:
    pid = query_params["pid"]
else:
    pid = None

if "clinicid" in query_params:
    clinicid = query_params["clinicid"]
else:
    clinicid = None

if eegid and clinicid and pid:
    st.session_state["eegid"] = eegid
    st.session_state["pid"] = pid
    st.session_state["clinicid"] = clinicid
    if "tab" in query_params:
        st.session_state['tab'] = query_params["tab"]
    st.switch_page("streamlit_apps/neurosynchrony.py")


if not eeg_id:
    # Title
    st.title("Queue")

    url = "https://app.sigmacomputing.com/embed/1-4j797MKZT5T7Xf8Wf5g8D5"

    html = f'<iframe src="{url}" frameborder="0" width="100%" height="900px"></iframe>'

    components.html(html, height=1000, scrolling=False)

    asyncio.run(access_eeg_data(eeg_id))

    eeg_visualization_dashboard()

    ecg_visualization_dashboard()

else:
    asyncio.run(access_eeg_data(eeg_id))

    if show_eeg:
        eeg_visualization_dashboard()

    elif show_ecg:
        ecg_visualization_dashboard()
    else:
        eeg_visualization_dashboard()
        ecg_visualization_dashboard()


# Footer section
version = get_version_from_pyproject()
footer_html = f"""
    <div style='position: fixed; bottom: 0; left: 0; padding: 10px;'>
        <span>Version: {version}</span>
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
