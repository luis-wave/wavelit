import os
import tempfile
from pathlib import Path
import streamlit as st
from mywaveanalytics.libraries import mywaveanalytics
from services.mywaveplatform_api import MyWavePlatformApi

class EEGDataManager:
    def __init__(self, base_url=None, username=None, password=None, api_key=None):
        self.api_service = MyWavePlatformApi(base_url, username, password, api_key)
        self.headers = self.api_service.login()

    def save_uploaded_file(self, uploaded_file):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                return tmp_file.name
        except Exception as e:
            st.error(f"Failed to save the uploaded file: {e}")
            return None

    def load_mw_object(self, path, eeg_type):
        try:
            mw_object = mywaveanalytics.MyWaveAnalytics(path, None, None, eeg_type)
            return mw_object
        except Exception as e:
            st.error(f"Loading failed for {path}: {e}")
            return None

    def save_eeg_data_to_session(self, mw_object, filename, eeg_id):
        st.session_state.mw_object = mw_object
        st.session_state.recording_date = mw_object.info['meas_date']
        st.session_state.filename = filename
        st.session_state.eeg_id = eeg_id

    def handle_uploaded_file(self, uploaded_file):
        saved_path = self.save_uploaded_file(uploaded_file)
        if saved_path:
            eeg_type = 0 if uploaded_file.name.lower().endswith(".dat") else 10 if uploaded_file.name.lower().endswith(".edf") else None
            if eeg_type is None:
                st.error("Unsupported file type.")
            else:
                mw_object = self.load_mw_object(saved_path, eeg_type)
                if mw_object:
                    st.success("EEG Data loaded successfully!")
                    self.save_eeg_data_to_session(mw_object, uploaded_file.name, None)

    def handle_downloaded_file(self, eeg_id):
        downloaded_path, file_extension = self.api_service.download_eeg_file(eeg_id, self.headers)
        if downloaded_path:
            st.success(f"EEG Data for ID {eeg_id} downloaded successfully!")
            eeg_type = 0 if file_extension.lower() == ".dat" else 10 if file_extension.lower() == ".edf" else None
            if eeg_type is not None:
                mw_object = self.load_mw_object(downloaded_path, eeg_type)
                if mw_object:
                    self.save_eeg_data_to_session(mw_object, downloaded_path, eeg_id)
            try:
                os.remove(downloaded_path)
            except Exception as e:
                st.error(f"Failed to delete the temporary file: {e}")

    def get_heart_rate_variables(self, eeg_id):
        return self.api_service.get_heart_rate_variables(eeg_id, self.headers)
