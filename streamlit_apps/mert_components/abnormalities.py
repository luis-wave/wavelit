"""
Sets up the component for noting abnormalities like AEA, AHR, MTHFR.
"""

import asyncio

import streamlit as st


@st.fragment
def render_abnormalities(data_manager):
    st.subheader("Abnormalities")

    converter = {
        "Possible Irregular EEG Activity (AEA)": "Possible Irregular EEG Activity",
        "Possible Irregular Heart Rhythm (AHR)": "Possible Irregular Heart Rhythm",
        "Possible MTHFR": "Possible MTHFR",
        "Heart Rate": "Heart Rate"
    }
    reverse_converter = {v: k for k, v in converter.items()}

    if (
        "eeg_reports" in st.session_state
        and "abnormalities" in st.session_state.eeg_reports
    ):
        abnormalities = st.session_state.eeg_reports["abnormalities"]
        if abnormalities:
            st.write("Existing Abnormalities:")
            for abnormality_id, abnormality in abnormalities.items():
                name = reverse_converter.get(
                    abnormality["name"], abnormality["name"].upper()
                )
                status = "Approved" if abnormality["isApproved"] else "Not Approved"

                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"- {name}: {status}")
                with col2:
                    if not abnormality["isApproved"]:
                        if st.button("Approve", key=f"approve_{abnormality_id}"):
                            asyncio.run(
                                data_manager.approve_abnormality(abnormality_id)
                            )
                            st.success(f"{name} has been approved.")
                            st.rerun()
                with col3:
                    if st.button("Delete", key=f"delete_{abnormality_id}"):
                        asyncio.run(data_manager.delete_abnormality(abnormality_id))
                        st.success(f"{name} has been deleted.")
                        st.rerun()
        else:
            st.write("No existing abnormalities found.")
    else:
        st.write("No abnormality data available.")

    with st.form("add_irregularity_form", border=True):
        options = st.multiselect(
            "Select irregularity", list(converter.keys()) + ["Other"]
        )
        other_input = None
        other_input = st.text_input("Please specify other irregularity:")
        submit_button = st.form_submit_button(label="Add")

        if submit_button:
            converted_options = [
                converter.get(option, option)
                for option in options
                if option != "Other"
            ]
            if other_input:
                converted_options.append(other_input)

            asyncio.run(data_manager.save_abnormalities(converted_options))
            st.success("Irregularities added successfully!")
            st.rerun()
