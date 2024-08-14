import numpy as np
import streamlit as st

from dsp.analytics import PersistPipeline, StandardPipeline


def eeg_epoch_visualization_dashboard():
    # Set page configuration
    # st.set_page_config(page_title="Epoch Visualizations", layout="wide")

    if "mw_object" not in st.session_state:
        st.error("Please load EEG data")
    else:
        st.title("EEG Epoch Generator")

        col1, col2 = st.columns(2)

        if st.session_state.filename and ("/tmp/" not in st.session_state.filename):
            col1.metric("Filename", st.session_state.filename)
        elif st.session_state.eeg_id:
            col1.metric("EEGId", st.session_state.eeg_id)

        col2.metric("Recording Date", st.session_state.recording_date)

        def run_persist_pipeline(mw_object):
            try:
                pipeline = PersistPipeline(mw_object)
                st.success("EEG Data loaded successfully!")
                return pipeline
            except Exception as e:
                st.error(f"Epoch analysis failed: {e}")

        # Check if `mw_object` is available
        if "mw_object" in st.session_state and st.session_state.mw_object:
            mw_object = st.session_state.mw_object.copy()

            eqi_pipeline = StandardPipeline(mw_object)
            eqi_pipeline.calculate_eqi()

            eqi = st.session_state.get("eqi", None)
            ref = st.session_state.get("ref", "le")

            time_win = 20

            if eqi is not None:
                if eqi > 80:
                    time_win = 20
                elif eqi > 60:
                    time_win = 15
                elif eqi > 50:
                    time_win = 10
                elif eqi < 50:
                    time_win = 5

            st.metric("EEG Quality Index", eqi)

            selected_ref_index = 0 if eqi is not None and eqi > 60 else 1
            ref_options = [
                "linked ears",
                "centroid",
                "bipolar transverse",
                "bipolar longitudinal",
            ]

            ref = st.selectbox(
                "Choose EEG reference", options=ref_options, index=selected_ref_index
            )

            reference_map = {
                "linked ears": "le",
                "centroid": "cz",
                "bipolar transverse": "btm",
                "bipolar longitudinal": "blm",
            }

            ref = reference_map.get(ref, "tcp")

            time_win = st.number_input(
                "Enter time window (seconds)",
                min_value=3,
                max_value=30,
                value=time_win,
                step=5,
            )


            if st.button("Generate top 20 epoch graphs"):
                with st.spinner("Running pipeline..."):
                    pipeline = run_persist_pipeline(mw_object)
                    if pipeline:
                        pipeline.run(ref=ref, time_win=time_win)
                        with st.spinner("Drawing..."):
                            pipeline.generate_graphs()
                            pipeline.reset(mw_object)

                pipeline.reset(mw_object)

        else:
            st.error(
                "No EEG data available. Please upload an EEG file on the main page."
            )


# To run the function as a Streamlit app
if __name__ == "__main__":
    eeg_epoch_visualization_dashboard()
