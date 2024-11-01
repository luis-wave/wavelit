import json
from copy import deepcopy
from datetime import datetime

import mne
import pandas as pd
import streamlit as st
from mywaveanalytics.libraries import mywaveanalytics as mwa
from mywaveanalytics.libraries import (
    filters,
    references
)

from access_control import get_version_from_pyproject
from data_models.abnormality_parsers import serialize_aea_to_pandas
from streamlit_dashboards import eeg_visualization_dashboard

st.set_page_config(layout="wide")

with open("synthetic_data/aea.json", "rb") as f:
    aea = json.load(f)
    aea_data = {
        "linked_ears": serialize_aea_to_pandas(
            aea.get("linked_ears"), ref="linked_ears"
        ),
        "centroid": serialize_aea_to_pandas(
            aea.get("centroid"), ref="centroid"
        ),
        "bipolar_longitudinal": serialize_aea_to_pandas(
            aea.get("bipolar_longitudinal"), ref="bipolar_longitudinal"
        ),
    }


def serialize_mw_to_df(mw_object, sample_rate=50, eeg=True, ecg=True):
    try:
        # Convert MyWaveObject MNE raw instance
        raw = mw_object

        # Select channels based on EEG or ECG type
        channels = raw.pick_types(eeg=eeg, ecg=ecg).ch_names
        raw.pick_channels(channels)

        # Downsample signal for better render speeds, lower sampling rates may impact graph spectral integrity.
        raw = raw.resample(sample_rate)
        df = raw.to_data_frame()
        df["time"] = df.index / sample_rate
        return df
    except Exception as e:
        st.error(f"Failed to convert EEG data to DataFrame: {e}")
        return None


def main():
    # Example of loading real EEG data from an EDF file
    edf_file_path = "synthetic_data/synthetic_eeg.edf"

    if "mw_object" not in st.session_state:
        
        # Assigning real data to MockMyWaveAnalytics object
        mw_object = mwa.MyWaveAnalytics(edf_file_path, None, None, 10)

        st.session_state.mw_object = mw_object
        st.session_state.recording_date = datetime.now().strftime("%b %d, %Y")
        st.session_state.filename = "Synthetic Oscillations"
        st.session_state.eeg_id = "EEG-123456789"
        st.session_state.eeg_graph = {
            "linked_ears": serialize_mw_to_df(
                mw_object.eeg
            ),
            "centroid": serialize_mw_to_df(
                references.centroid(
                    mw_object.copy().eeg
                )
            ),
            "bipolar_longitudinal": serialize_mw_to_df(
                references.temporal_central_parasagittal(
                    mw_object.copy().eeg
                )
            ),
        }
        st.session_state.aea = aea_data
        st.session_state.user = "Nicolas Cage"

    eeg_visualization_dashboard()

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
