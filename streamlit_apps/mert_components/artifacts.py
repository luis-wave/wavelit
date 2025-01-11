"""
Note abnormalities common in EEG review.
"""

import asyncio

import streamlit as st


def get_artifact_map():
    return {
        "ecg": "Electrocardiographic interference (ECG)",
        "excessiveMuscleTension": "Excessive muscle tension (EMG)",
        "eyeWandering": "Eye wandering",
        "eog": "Eyeblink artifact (EOG)",
        "foreheadTension": "Forehead tension",
        "earclips": "Improper ear clip (A1/A2) set-up",
        "jawTension": "Jaw tension",
        "leadWandering": "Lead wandering",
        "movement": "Movement",
        "neckTension": "Neck tension",
        "possibleDrowsiness": "Possible drowsiness",
        "powerlineInterference": "Powerline interference",
        "Please note that possible artifact distortion may be present due to the following reasons: potential drowsiness, poor EEG setup, and/or noncompliance.": "Please note that possible artifact distortion may be present due to the following reasons: potential drowsiness, poor EEG setup, and/or noncompliance.",
        "Please note that possible artifact distortion may be present due to a flat channel(s) that may be a consequence of EEG setup, maintenance, or instrumentation.": "Please note that possible artifact distortion may be present due to a flat channel(s) that may be a consequence of EEG setup, maintenance, or instrumentation."
    }


def translate_artifact_name(artifact_name):
    artifact_map = get_artifact_map()
    return artifact_map.get(artifact_name, artifact_name.capitalize())


@st.fragment
def render_artifact_distortions(data_manager):
    st.subheader("Artifact Distortions")

    if (
        "eeg_reports" in st.session_state
        and "artifacts" in st.session_state.eeg_reports
    ):
        artifacts = st.session_state.eeg_reports["artifacts"]
        if artifacts:
            st.write("Existing Artifacts:")
            for artifact_id, artifact_info in artifacts.items():
                full_label = translate_artifact_name(artifact_info["name"])
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"- {full_label}")
                with col2:
                    if st.button("Delete", key=f"delete_artifact_{artifact_id}"):
                        asyncio.run(data_manager.delete_artifact(artifact_id))
                        st.success(f"{full_label} has been deleted.")
                        st.rerun()
        else:
            st.write("No existing artifacts found.")
    else:
        st.write("No artifact data available.")

    #with st.popover("Add artifacts", use_container_width=True):
    with st.form("add_artifact_form", border=True):
        artifact_map = get_artifact_map()
        reverse_artifact_map = {v: k for k, v in artifact_map.items()}

        options = st.multiselect(
            "Add artifact distortion", list(artifact_map.values()) + ["Other"]
        )
        other_input = None
        other_input = st.text_input("Please specify other artifact:")

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            artifacts = [
                reverse_artifact_map.get(option, option)
                for option in options
                if option != "Other"
            ]
            if other_input:
                artifacts.append(other_input)
            asyncio.run(data_manager.save_artifact_distortions(artifacts))
            st.success("Artifacts saved successfully!")
            st.rerun()
