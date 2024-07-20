import asyncio

import streamlit as st
import streamlit.components.v1 as components

from access_control import access_eeg_data
from streamlit_dashboards import (ecg_visualization_dashboard,
                                  eeg_epoch_visualization_dashboard,
                                  eeg_visualization_dashboard)

# Streamlit app setup
#st.set_page_config(page_title="Neuroref Report Dashboard", layout="wide")

# Check if query parameters exist and set eeg_id if available
query_params = st.query_params.to_dict()
if "eegId" in query_params:
    eeg_id = query_params["eegId"]
    st.write(eeg_id)
else:
    eeg_id = None

if not eeg_id:

    # Title
    st.title("EEG Reports Dashboard")


    url = "https://app.sigmacomputing.com/embed/1-7katQ0rNGbMSHasd6Gzc25"

    html=f'<iframe src="{url}" width="100%" height="900px"></iframe>'


    components.html(html,height=1000,scrolling=False)

    asyncio.run(access_eeg_data(eeg_id))

    eeg_visualization_dashboard()

    ecg_visualization_dashboard()

    eeg_epoch_visualization_dashboard()

else:
    asyncio.run(access_eeg_data(eeg_id))

    eeg_visualization_dashboard()

    ecg_visualization_dashboard()

    eeg_epoch_visualization_dashboard()