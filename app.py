from pathlib import Path

import streamlit as st
from mywaveanalytics import MyWaveAnalytics

from pipeline import PersistPipeline


def run_persist_pipeline(path, eeg_type):
    try:
        mw_object = MyWaveAnalytics(path, None, None, eeg_type)
        PersistPipeline(mw_object)
        st.success("Persist pipeline executed successfully!")
    except Exception as e:
        st.error(f"Persist pipeline failed for {path}: {e}")


import tempfile


def save_uploaded_file(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(uploaded_file.name).suffix
        ) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Failed to save the uploaded file: {e}")
        return None


st.title("EEG Epoch Generator")

uploaded_file = st.file_uploader("Upload an EEG file", type=["dat", "edf"])
if uploaded_file is not None:
    file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type}
    st.write(file_details)

    # Save uploaded file to disk to make it accessible by file path
    saved_path = save_uploaded_file(uploaded_file)
    if saved_path:
        # Determine EEG type based on file extension
        eeg_type = (
            0
            if uploaded_file.name.lower().endswith(".dat")
            else 10
            if uploaded_file.name.lower().endswith(".edf")
            else None
        )
        if eeg_type is None:
            st.error("Unsupported file type.")
        else:
            with st.spinner("Running analysis..."):
                run_persist_pipeline(saved_path, eeg_type)
    else:
        st.error("Failed to process the uploaded file.")
