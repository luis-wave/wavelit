import json
from copy import deepcopy
from datetime import datetime

import mne
import pandas as pd
import streamlit as st

from access_control import get_version_from_pyproject
from mywaveanalytics.libraries import mywaveanalytics as mwa
from mywaveanalytics.libraries import filters, references
from streamlit_dashboards import ecg_visualization_dashboard

from mywavelab.libraries import mywavelab as mwl

st.set_page_config(layout="wide")

def main():
    eeg_file_path = input("Paste an edf or deymed file path -> ")

    # Assigning real data to MockMyWaveAnalytics object
    mw_object = mwa.MyWaveAnalytics("synthetic_data/synthetic_eeg.edf", None, None, 10)
    mwl_object = mwl.MyWaveLab(eeg_file_path)
    hrv = mwl_object.ecg_stats()

    st.session_state['hrv_stats'] = hrv
    st.session_state['heart_rate'] = 000.00
    st.session_state['heart_rate_std_dev'] = 00.00

    st.session_state.mw_object = mw_object
    st.session_state.recording_date = datetime.now().strftime("%b %d, %Y")
    st.session_state.filename = "Synthetic Oscillations"
    st.session_state.eeg_id = "EEG-123456789"
    st.session_state.user = "Nicolas Cage"

    ecg_visualization_dashboard()

    # Footer section
    version = get_version_from_pyproject()
    footer_html = f"""
        <div style='position: fixed; bottom: 0; left: 0; padding: 10px;'>
            <span>Version: {version}</span>
        </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
