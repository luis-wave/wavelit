# epochs.py

import mne
import numpy as np
import streamlit as st
from pipeline import PersistPipeline

st.set_page_config(page_title="EEG Epoch Generator", layout="wide")

st.title("EEG Epoch Generator")

def run_persist_pipeline(mw_object):
    try:
        pipeline = PersistPipeline(mw_object)
        st.success("EEG Data loaded successfully!")
        return pipeline
    except Exception as e:
        st.error(f"Epoch analysis failed: {e}")

# Check if `mw_object` is available
if 'mw_object' in st.session_state and st.session_state.mw_object:
    mw_object = st.session_state.mw_object
    mw_object = mw_object.copy()

    eqi = st.session_state.get('eqi', None)
    ref = st.session_state.get('ref', 'le')
    time_win = st.session_state.get('time_win', 20)

    if eqi < 60:
        time_win = 20
    if eqi < 40:
        time_win = 10
    if eqi < 20:
        time_win = 5

    st.subheader(f"EEG Quality Index: {eqi}")

    selected_ref_index = 0 if eqi > 60 else 1
    ref_options = [
        "linked ears",
        "centroid",
        "bipolar transverse",
        "bipolar longitudinal"
    ]

    ref = st.selectbox(
        "Choose EEG reference",
        options=ref_options,
        index=selected_ref_index
    )

    if ref == "linked ears":
        ref = "le"
    elif ref == "centroid":
        ref = "cz"
    elif ref == "bipolar transverse":
        ref = "btm"
    elif ref == "bipolar longitudinal":
        ref = "blm"
    else:
        ref = "tcp"

    time_win = st.number_input(
        "Enter time window (seconds)",
        min_value=3,
        max_value=30,
        value=time_win,
        step=5
    )

    pipeline = run_persist_pipeline(mw_object)

    if st.button("Generate graphs"):
        with st.spinner("Drawing..."):
            pipeline.run(ref=ref, time_win=time_win)
            pipeline.generate_graphs()
            pipeline.reset(mw_object)

else:
    st.error("No EEG data available. Please upload an EEG file on the main page.")
