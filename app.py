import tempfile
from pathlib import Path

import streamlit as st
from mywaveanalytics import MyWaveAnalytics
from mywaveanalytics.libraries import eeg_computational_library, references, filters
from mywaveanalytics.pipelines import ngboost_protocol_pipeline

from pipeline import PersistPipeline


def calculate_eqi(mw_object):
    try:
        mw_copy = mw_object.copy()
        filters.eeg_filter(mw_copy, 1, 25)
        filters.notch(mw_copy)
        filters.resample(mw_copy)
        tcp_eeg = references.temporal_central_parasagittal(mw_copy)

        eqi_features, z_scored_eqi = eeg_computational_library.calculate_eqi(tcp_eeg)
        eqi_predictions, eqi_score = eeg_computational_library.eqi_svm_inference(
            z_scored_eqi
        )

        return eqi_score
    except Exception as e:
        st.error(f"EEG quality assesment failed for the following reason: {e}")


def load_mw_object(path, eegtype):
    try:
        mw_object = MyWaveAnalytics(path, None, None, eegtype)
    except Exception as e:
        st.error(f"Loading failed for {path}: {e}")
    return mw_object


def run_persist_pipeline(mw_object):
    try:
        pipeline = PersistPipeline(mw_object)
        st.success("EEG Data loaded successfully!")
        return pipeline
    except Exception as e:
        st.error(f"Epoch analysis failed for {path}: {e}")


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
            mw_object = load_mw_object(saved_path, eeg_type)

            eqi = calculate_eqi(mw_object)

            st.write(f"EEG Quality Index: {eqi}")
            selected_ref_index = 0

            if eqi < 60:
                selected_ref_index = 1

            # EEG Reference selector
            ref = st.selectbox(
                "Choose EEG reference",
                options=[
                    "linked ears",
                    "centroid",
                    "bipolar_transverse",
                    "bipolar longitudinal"
                ],
                index=selected_ref_index,
            )

            if eqi >= 80:
                time_window_length = 20
            if eqi < 80:
                time_window_length = 15
            if eqi < 60:
                time_window_length = 10
            if eqi < 20:
                time_window_length = 5

            # Time window input
            time_win = st.number_input(
                "Enter time window (seconds)",
                min_value=3,
                max_value=30,
                value=time_window_length,
                step=5,
            )

            if ref == "linked ears":
                ref = "le"
            elif ref == "centroid":
                ref = "cz"
            elif ref == "bipolar_transverse":
                ref = "btm"
            elif ref == "bipolar longitudinal":
                ref = "blm"
            else:
                ref = "tcp"

            pipeline = run_persist_pipeline(mw_object)

            # Button to execute pipeline
            if st.button("Generate epochs graphs"):
                with st.spinner("Drawing..."):
                    pipeline.run(ref=ref, time_win=time_win)
                    pipeline.generate_graphs()
                    pipeline.reset(mw_object)
    else:
        st.error("Failed to process the uploaded file.")
