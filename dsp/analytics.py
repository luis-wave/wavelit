from mywaveanalytics.libraries import (ecg_statistics,
                                       eeg_computational_library, filters,
                                       mywaveanalytics, references)
import streamlit as st


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
        self.preprocessing()
        with st.spinner("Calculate EEG Quality Index (EQI)..."):
            self.calculate_eqi()
        with st.spinner("Calculate heart rate measures..."):
            self.calculate_heart_rate()

    def preprocessing(self):
        # Apply EEG filters
        filters.eeg_filter(self.mw_object, 1, None)  # Ensure the second parameter is correct
        filters.notch(self.mw_object)
        filters.resample(self.mw_object)

    def calculate_eqi(self):
        try:
            # Calculate EEG quality index
            tcp_eeg = references.temporal_central_parasagittal(self.mw_object)
            eqi_features, z_scored_eqi = eeg_computational_library.calculate_eqi(tcp_eeg)
            eqi_predictions, eqi_score = eeg_computational_library.eqi_svm_inference(z_scored_eqi)
            st.session_state.eqi = eqi_score
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