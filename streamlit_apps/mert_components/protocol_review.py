"""
Set up protocol approval/rejection process. Enable the editing of treatment parameters within certain thresholds.
"""

import asyncio
from datetime import datetime

import pandas as pd
import streamlit as st

from .review_utils import EEGReviewState, mert2_user


@st.fragment
def render_protocol_page(data_manager):
    st.title("EEG Protocol")

    # Fetch EEG info
    eeg_info = asyncio.run(data_manager.fetch_eeg_info_by_patient_id_and_eeg_id())
    base_protocol = eeg_info["baseProtocol"]
    analysis_meta = eeg_info["eegInfo"]["analysisMeta"]
    eeg_info_data = eeg_info["eegInfo"]

    current_state = (
        EEGReviewState[analysis_meta["reviewState"]]
        if analysis_meta["reviewState"]
        else EEGReviewState.PENDING
    )

    if "protocol" in eeg_info:
        protocol_data = eeg_info["protocol"]

        phases_data = protocol_data["phases"][0]

        if "approvedByName" in protocol_data:
            approver_name = protocol_data["approvedByName"]
            st.markdown(f"**Approved by:** {approver_name}")

        if "isRejected" in protocol_data:
            st.markdown("**Protocol is REJECTED**")

        if "isRejected" not in protocol_data:
            st.markdown("**Protocol is PENDING**")
    else:
        protocol_data = None

    # Fetch doctor approval state
    doctor_approval_state = asyncio.run(data_manager.get_doctor_approval_state())

    if analysis_meta and "reviewerStaffId" in analysis_meta:
        first_reviewer = mert2_user.get(analysis_meta["reviewerStaffId"], "N/A")
    else:
        first_reviewer = "N/A"

    if analysis_meta and "secondReviewerStaffId" in analysis_meta:
        second_reviewer = mert2_user.get(analysis_meta["secondReviewerStaffId"], "N/A")
    else:
        second_reviewer = "N/A"

    # Display metadata
    st.subheader("Metadata")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**EEG ID:** {eeg_info_data['eegId']}")
        st.markdown(f"**Patient ID:** {data_manager.patient_id}")
        st.markdown(f"**Clinic ID:** {data_manager.clinic_id}")
    with col2:
        st.markdown(f"**Recording Date:** {base_protocol['recordingDate']}")
        st.markdown(f"**Upload Date:** {eeg_info_data['uploadDateTime']}")
        st.markdown(f"**Review State:** {analysis_meta['reviewState']}")

    # Display doctor approval state
    st.subheader("Doctor Approval State")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Clinician**")
        st.markdown(f"Approved: {doctor_approval_state['clinician']['approved']}")
        st.markdown(f"Date: {doctor_approval_state['clinician']['datetime'] or 'N/A'}")
        st.markdown(
            f"Name: {doctor_approval_state['clinician']['firstName'] or 'N/A'} {doctor_approval_state['clinician']['lastName'] or 'N/A'}"
        )
    with col2:
        st.markdown("**Physician**")
        st.markdown(f"Approved: {doctor_approval_state['physician']['approved']}")
        st.markdown(f"Date: {doctor_approval_state['physician']['datetime'] or 'N/A'}")
        st.markdown(
            f"Name: {doctor_approval_state['physician']['firstName'] or 'N/A'} {doctor_approval_state['physician']['lastName'] or 'N/A'}"
        )

    # Create editable dataframe for base protocol
    st.subheader("Base Protocol")

    # Add new fields to the protocol
    base_protocol["pulseMode"] = base_protocol.get("pulseMode", "Biphasic")
    base_protocol["location"] = base_protocol.get("location", "F1-FZ-F2")

    if protocol_data:
        if "MONO" in phases_data["pulseParameters"]["phase"]:
            phases_data["pulseMode"] = "Monophasic"
        else:
            phases_data["pulseMode"] = "Biphasic"
        phases_data.pop("pulseParameters")
        protocol_df = pd.DataFrame([phases_data])
    else:
        protocol_df = pd.DataFrame([base_protocol])

    # Define the location options
    location_options = [
        "FP1-FPZ-FP2",
        "F1-FZ-F2",
        "C1-CZ-C2",
        "P1-PZ-P2",
        "F1-F3-F5",
        "F2-F4-F6",
        "F7-FT7-T3",
        "F8-FT8-T4",
        "CP1-CPZ-CP2",
        "FC1-FCZ-FC2",
        "TP7-T3-FT7",
        "TP8-T4-FT8",
        "C5-C3-C1",
        "C6-C4-C2",
        "C3-CP3-P3",
        "C4-CP4-P4",
        "P3-CP5-T3",
        "P4-CP6-T4",
        "P1-P3-P5",
        "P2-P4-P6",
        "P3-P5-P7",
        "P4-P6-P8",
        "P3-PO3-O1",
        "P4-PO4-O2",
        "PO3-O1-PO7",
        "PO4-O2-PO8",
    ]

    with st.form("protocol_data_editor_form", border=False):
        # Create the editable dataframe
        edited_df = st.data_editor(
            protocol_df,
            num_rows="fixed",
            use_container_width=True,
            disabled=["recordingDate"],
            column_config={
                "pulseMode": st.column_config.SelectboxColumn(
                    "Pulse Mode", options=["Biphasic", "Monophasic"], required=True
                ),
                "location": st.column_config.SelectboxColumn(
                    "Location", options=location_options, required=True
                ),
                "protocol": st.column_config.NumberColumn(
                    "Protocol (Hz)", min_value=8, max_value=13, step=0.1
                ),
            },
            hide_index=True,
        )

        # Check if there are changes in the protocol
        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("Save Protocol Changes"):
                try:
                    # Convert the edited dataframe to a dictionary
                    updated_protocol = edited_df.iloc[0].to_dict()

                    # Prepare the protocol object
                    protocol = {
                        "acknowledgeState": {
                            "clinician": doctor_approval_state["clinician"],
                            "physician": doctor_approval_state["physician"],
                        },
                        "approvedByName": st.session_state["name"],
                        "approvedDate": datetime.utcnow().isoformat() + "Z",
                        "createdByName": st.session_state["name"],
                        "createdDate": datetime.utcnow().isoformat() + "Z",
                        "eegId": data_manager.eeg_id,
                        "numPhases": 1,
                        "patientId": data_manager.patient_id,
                        "phases": [
                            {
                                "location": updated_protocol["location"],
                                "goalIntensity": updated_protocol.get(
                                    "goalIntensity", 0
                                ),
                                "pulseParameters": {
                                    "phase": "MONO"
                                    if updated_protocol["pulseMode"] == "Monophasic"
                                    else "BIPHASIC"
                                },
                                "frequency": updated_protocol["frequency"],
                                "burstDuration": updated_protocol.get("burstDuration"),
                                "burstFrequency": updated_protocol.get(
                                    "burstFrequency"
                                ),
                                "burstNumber": updated_protocol.get("burstNumber"),
                                "interBurstInterval": updated_protocol.get(
                                    "interBurstInterval"
                                ),
                                "interTrainInterval": updated_protocol[
                                    "interTrainInterval"
                                ],
                                "phaseDuration": updated_protocol.get(
                                    "phaseDuration", 0
                                ),
                                "trainDuration": updated_protocol["trainDuration"],
                                "trainNumber": updated_protocol["trainNumber"],
                            }
                        ],
                        "subtype": "CORTICAL",
                        "totalDuration": updated_protocol.get("totalDuration", 0),
                        "type": "TREATMENT",
                    }

                    # Call the save_protocol method
                    asyncio.run(data_manager.save_protocol(protocol))

                    # Ran twice to complete, protocol review by eeg scientist
                    asyncio.run(data_manager.save_protocol(protocol))

                    asyncio.run(
                        data_manager.update_eeg_review(
                            is_first_reviewer=(current_state == EEGReviewState.PENDING),
                            state=EEGReviewState.CLINIC_REVIEW.name,
                        )
                    )
                    st.success("Protocol updated successfully!")
                except Exception as e:
                    st.error(f"Failed to update protocol: {str(e)}")

        with col2:
            rejection_reason = st.text_input("Rejection Reason")
            if st.form_submit_button("Reject Protocol"):
                if rejection_reason:
                    try:
                        updated_protocol = protocol_df.iloc[0].to_dict()

                        # Prepare the protocol object (same as in the save function)
                        protocol = {
                            "acknowledgeState": {"clinician": "", "physician": ""},
                            "approvedByName": "",
                            "approvedDate": "",
                            "createdByName": "",
                            "createdDate": "",
                            "eegId": data_manager.eeg_id,
                            "numPhases": 1,
                            "patientId": data_manager.patient_id,
                            "phases": [
                                {
                                    "location": updated_protocol["location"],
                                    "goalIntensity": updated_protocol.get(
                                        "goalIntensity", 0
                                    ),
                                    "pulseParameters": {
                                        "phase": "MONO"
                                        if updated_protocol["pulseMode"] == "Monophasic"
                                        else "BIPHASIC"
                                    },
                                    "frequency": updated_protocol["frequency"],
                                    "burstDuration": None,
                                    "burstFrequency": None,
                                    "burstNumber": None,
                                    "interBurstInterval": None,
                                    "interTrainInterval": updated_protocol[
                                        "interTrainInterval"
                                    ],
                                    "phaseDuration": updated_protocol.get(
                                        "phaseDuration", 0
                                    ),
                                    "trainDuration": updated_protocol["trainDuration"],
                                    "trainNumber": updated_protocol["trainNumber"],
                                }
                            ],
                            "subtype": "CORTICAL",
                            "totalDuration": updated_protocol.get("totalDuration", 0),
                            "type": "TREATMENT",
                        }

                        # Call the reject_protocol method
                        asyncio.run(
                            data_manager.reject_protocol(rejection_reason, protocol)
                        )
                        st.success("Protocol rejected successfully!")
                    except Exception as e:
                        st.error(f"Failed to reject protocol: {str(e)}")
                else:
                    st.warning("Please provide a rejection reason.")

    # Display additional EEG information
    st.subheader("Additional EEG Information")
    st.markdown(f"**File Name:** {eeg_info_data['fileName']}")
    st.markdown(f"**Is Import:** {'Yes' if eeg_info_data['isImport'] else 'No'}")
    st.markdown(f"**Is Processed:** {'Yes' if eeg_info_data['isProcessed'] else 'No'}")
    st.markdown(f"**Quality Status:** {eeg_info_data['qualityStatus'] or 'N/A'}")

    # Display review information
    st.subheader("Review Information")
    st.markdown(f"**Review Deadline:** {analysis_meta['reviewDeadline']}")
    st.markdown(f"**Reviewer:** {first_reviewer}")
    st.markdown(f"**Review Date:** {analysis_meta['reviewDatetime']}")
    st.markdown(f"**Second Reviewer:** {second_reviewer}")
    st.markdown(
        f"**Second Review Date:** {analysis_meta['secondReviewDatetime'] or 'N/A'}"
    )
