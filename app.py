from pathlib import Path

import streamlit as st
from mywaveanalytics import MyWaveAnalytics

from pipeline import PersistPipeline


def run_persist_pipeline(path, eeg_type):
    try:
        mw_object = MyWaveAnalytics(path, None, None, eeg_type)
        pipeline = PersistPipeline(mw_object)
        st.success("EEG Data loaded successfully!")
        return pipeline, mw_object
    except Exception as e:
        st.error(f"Loading failed for {path}: {e}")


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
            # EEG Reference selector
            ref = st.selectbox(
                "Choose EEG reference",
                options=["linked ears", "centroid", "bipolar transverse"],
                index=0,
            )
            # Time window input
            time_win = st.number_input(
                "Enter time window (seconds)", min_value=1, value=30, step=1
            )

            if ref == "linked ears":
                ref = "le"
            elif ref == "centroid":
                ref = "cz"
            else:
                ref = "tcp"

            pipeline, mw_object = run_persist_pipeline(saved_path, eeg_type)

            # Button to execute pipeline
            if st.button("Generate epochs graphs"):
                with st.spinner("Drawings graphs..."):
                    pipeline.run(ref=ref, time_win=time_win)
                    pipeline.generate_graphs()
                    pipeline.reset(mw_object)
    else:
        st.error("Failed to process the uploaded file.")
