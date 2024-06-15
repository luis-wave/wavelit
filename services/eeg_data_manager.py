import asyncio
import os
import tempfile
from datetime import datetime
from pathlib import Path
import pandas as pd

import streamlit as st
from mywaveanalytics.libraries import mywaveanalytics
from mywaveanalytics.libraries.references import centroid, bipolar_longitudinal_montage
from mywaveanalytics.utils import params


from dsp.analytics import StandardPipeline
from services.mywaveplatform_api import MyWavePlatformApi
from utils.helpers import format_single




# Function to convert a MyWaveAnalytics object to a DataFrame with resampling
@st.cache_data
def mw_to_dataframe_resampled(_mw_object, sample_rate=50, channels=params.CHANNEL_ORDER_EEG):
    try:
        raw = _mw_object.eeg
        raw.pick_channels(channels)
        raw = raw.resample(sample_rate)
        df = raw.to_data_frame()
        df['time'] = df.index / sample_rate
        return df
    except Exception as e:
        st.error(f"Failed to convert EEG data to DataFrame: {e}")
        return None





class EEGDataManager:
    def __init__(self, base_url=None, username=None, password=None, api_key=None):
        self.api_service = MyWavePlatformApi(base_url, username, password, api_key)
        st.session_state.heart_rate = None
        st.session_state.eqi = None
        st.session_state.aea = None
        st.session_state.ahr = None
        st.session_state.autoreject = None
        st.session_state.heart_rate = None
        st.session_state.heart_rate_std_dev = None


    async def initialize(self):
        self.headers = await self.api_service.login()

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

    @st.cache_data
    def save_eeg_data_to_session(_self, _mw_object, filename, eeg_id):
        st.session_state.mw_object = _mw_object
        st.session_state.recording_date = datetime.strptime(_mw_object.recording_date, "%Y-%m-%d").strftime("%b %d, %Y")
        st.session_state.filename = filename
        st.session_state.eeg_id = eeg_id
        st.session_state.eeg_graph = {
            "linked_ears": mw_to_dataframe_resampled(_mw_object.copy()),
            "centroid": mw_to_dataframe_resampled(centroid(_mw_object.copy())),
            "bipolar_longitudinal": mw_to_dataframe_resampled(bipolar_longitudinal_montage(_mw_object.copy()))
        }
        st.session_state.ecg_graph = mw_to_dataframe_resampled(_mw_object.copy(), channels=['ECG'])

    async def handle_uploaded_file(self, uploaded_file):
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
                    pipeline = StandardPipeline(mw_object)
                    pipeline.run()

    async def handle_downloaded_file(self, eeg_id):
        downloaded_path, file_extension = await self.api_service.download_eeg_file(eeg_id, self.headers)
        if downloaded_path:
            st.success(f"EEG Data for ID {eeg_id} downloaded successfully!")
            eeg_type = 0 if file_extension.lower() == ".dat" else 10 if file_extension.lower() == ".edf" else None
            if eeg_type is not None:
                mw_object = self.load_mw_object(downloaded_path, eeg_type)
                if mw_object:
                    self.save_eeg_data_to_session(mw_object, downloaded_path, eeg_id)
                    pipeline = StandardPipeline(mw_object)
                    pipeline.run()
                st.success("Saved eeg data to session")
            try:
                os.remove(downloaded_path)
            except Exception as e:
                st.error(f"Failed to delete the temporary file: {e}")

    async def get_heart_rate_variables(self, eeg_id):
        return await self.api_service.get_heart_rate_variables(eeg_id, self.headers)

    async def fetch_additional_data(self, eeg_id):
        ahr, aea, autoreject = await asyncio.gather(
            self.api_service.get_ahr_onsets(eeg_id, self.headers),
            self.api_service.get_aea_onsets(eeg_id, self.headers),
            self.api_service.get_autoreject_annots(eeg_id, self.headers)
        )
        st.session_state.ahr = ahr
        st.session_state.aea = aea
        st.session_state.autoreject = autoreject





def filter_predictions(predictions, confidence_threshold=0.9, epoch_length=0.7):
    # Extract the probabilities array from the dictionary
    probabilities = predictions['predictions']
    r_peaks = predictions['r_peaks']

    # Initialize lists to store the data
    onsets = []
    confidences = []
    is_seizure = []

    # Iterate through the probabilities to find values above the threshold
    for index, probability in enumerate(probabilities):
        if probability > confidence_threshold:
            onsets.append(r_peaks[index])
            confidences.append(probability)
            is_seizure.append(True)
        else:
            # Append data for all lists even if they do not meet the threshold
            onsets.append(index * epoch_length)
            confidences.append(probability)
            is_seizure.append(False)

    # Create a DataFrame with the collected data
    df = pd.DataFrame({
        'onsets': onsets,
        'probability': confidences,
        'is_arrythmia': is_seizure
    })

    df['ahr_times'] = df['onsets'].apply(format_single)

    return df