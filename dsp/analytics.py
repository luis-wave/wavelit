from mywaveanalytics.libraries import (ecg_statistics,
                                       eeg_computational_library, filters,
                                       mywaveanalytics, references)
import streamlit as st
from mywaveanalytics.pipelines import eqi_pipeline


if 'eqi' not in st.session_state:
    st.session_state.eqi = None
if 'heart_rate' not in st.session_state:
    st.session_state.heart_rate = None
if 'heart_rate_std_dev' not in st.session_state:
    st.session_state.heart_rate_std_dev = None



class StandardPipeline:
    def __init__(self, mw_object):
        self.mw_object = mw_object.copy()

    def run(self):
        with st.spinner("Calculate EEG Quality Index (EQI)..."):
            self.calculate_eqi()
        with st.spinner("Calculate heart rate measures..."):
            self.calculate_heart_rate()

    def calculate_eqi(self):
        try:
            # Calculate EEG quality index
            pipeline = eqi_pipeline.QAPipeline(self.mw_object)
            pipeline.run()
            analysis = pipeline.analysis_json
            st.session_state.eqi = analysis['eqi_score']
        except Exception as e:
            st.error(f"EEG quality assessment failed for the following reason: {e}")

    def calculate_heart_rate(self):
        try:
            # Filter ECG signal before deriving heart rate measures
            ecg_events_loc = filters.ecgfilter(self.mw_object)
            # Find heart rate and its standard deviation
            heart_rate_bpm, heart_rate_std_dev = ecg_statistics.ecg_bpm(ecg_events_loc)
            st.session_state.heart_rate = heart_rate_bpm
            st.session_state.heart_rate_std_dev = heart_rate_std_dev
        except Exception as e:
            st.error(f"Heart rate calculation failed for the following reason: {e}")