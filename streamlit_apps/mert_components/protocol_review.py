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

    # Create multiple protocol phase tables
    if protocol_data and "phases" in protocol_data:
        phases = protocol_data["phases"]
    else:
        # If no protocol data, create a single phase from base protocol
        base_protocol["pulseMode"] = base_protocol.get("pulseMode", "Biphasic")
        base_protocol["location"] = base_protocol.get("location", "F1-FZ-F2")
        phases = [base_protocol]

    # Add a button to add new phase
    if st.button("Add Phase", key="add_phase_button"):
        try:
            # Create a new phase based on the last phase's data
            last_phase = phases[-1].copy()

            # Prepare the protocol object with the additional phase
            current_protocol = {
                "acknowledgeState": {
                    "clinician": doctor_approval_state["clinician"],
                    "physician": doctor_approval_state["physician"],
                },
                "approvedByName": st.session_state["name"],
                "approvedDate": datetime.utcnow().isoformat() + "Z",
                "createdByName": st.session_state["name"],
                "createdDate": datetime.utcnow().isoformat() + "Z",
                "eegId": data_manager.eeg_id,
                "numPhases": len(phases) + 1,
                "patientId": data_manager.patient_id,
                "phases": [*phases, last_phase],
                "subtype": "CORTICAL",
                "type": "TREATMENT",
            }

            # Save the protocol with the new phase
            asyncio.run(data_manager.save_protocol(current_protocol))
            asyncio.run(data_manager.save_protocol(current_protocol))  # Run twice as per original code

            # Refresh the page to show the new phase
            st.rerun()
        except Exception as e:
            st.error(f"Failed to add new phase: {str(e)}")

    edited_phases = []

    # Display each phase's data editor
    for i, phase in enumerate(phases):
        st.subheader(f"Phase {i + 1}")

        # Add pulseMode to phase data
        if "pulseParameters" in phase:
            phase["pulseMode"] = "Monophasic" if "MONO" in phase["pulseParameters"]["phase"] else "Biphasic"
        else:
            phase["pulseMode"] = "Biphasic"

        # Convert phase to DataFrame
        phase_df = pd.DataFrame([phase])

        # Create editable table for each phase - Added unique key
        edited_df = st.data_editor(
            phase_df,
            num_rows="fixed",
            use_container_width=True,
            key=f"phase_{i}_editor",  # Added unique key based on phase index
            disabled=["recordingDate"] if "recordingDate" in phase_df.columns else [],
            column_config={
                "pulseMode": st.column_config.SelectboxColumn(
                    "Pulse Mode", options=["Biphasic", "Monophasic"], required=True
                ),
                "location": st.column_config.SelectboxColumn(
                    "Location", options=location_options, required=True
                ),
                "frequency": st.column_config.NumberColumn(
                    "Frequency (Hz)", min_value=8, max_value=13, step=0.1
                ),
                "trainDuration": st.column_config.NumberColumn(
                    "Train Duration (s)", min_value=1, step=1
                ),
                "trainNumber": st.column_config.NumberColumn(
                    "Train Number", min_value=1, step=1
                ),
                "interTrainInterval": st.column_config.NumberColumn(
                    "Inter-Train Interval (s)", min_value=1, step=1
                ),
            },
            hide_index=True,
        )
        edited_phases.append(edited_df.iloc[0].to_dict())

    # Create a separate form for actions
    with st.form("protocol_actions_form"):
        rejection_reason = st.text_input("Rejection Reason", key="rejection_reason_input")

        # Add form submit buttons
        col1, col2 = st.columns(2)
        with col1:
            save_submitted = st.form_submit_button("Save Protocol Changes")
        with col2:
            reject_submitted = st.form_submit_button("Reject Protocol")

    # Handle form submissions
    if save_submitted:
        try:
            # Prepare the protocol object with multiple phases
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
                "numPhases": len(edited_phases),
                "patientId": data_manager.patient_id,
                "phases": [
                    {
                        "location": phase["location"],
                        "goalIntensity": phase.get("goalIntensity", 0),
                        "pulseParameters": {
                            "phase": "MONO" if phase["pulseMode"] == "Monophasic" else "BIPHASIC"
                        },
                        "frequency": phase["frequency"],
                        "burstDuration": phase.get("burstDuration", 0),
                        "burstFrequency": phase.get("burstFrequency", 0),
                        "burstNumber": phase.get("burstNumber", 0),
                        "interBurstInterval": phase.get("interBurstInterval", 0),
                        "interTrainInterval": phase["interTrainInterval"],
                        "phaseDuration": phase.get("phaseDuration", 0),
                        "trainDuration": phase["trainDuration"],
                        "trainNumber": phase["trainNumber"],
                    }
                    for phase in edited_phases
                ],
                "subtype": "CORTICAL",
                "totalDuration": sum(phase.get("totalDuration", 0) for phase in edited_phases),
                "type": "TREATMENT",
            }

            # Save the protocol
            asyncio.run(data_manager.save_protocol(protocol))
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

    if reject_submitted:
        if rejection_reason:
            try:
                protocol = {
                    "acknowledgeState": {"clinician": "", "physician": ""},
                    "approvedByName": "",
                    "approvedDate": "",
                    "createdByName": "",
                    "createdDate": "",
                    "eegId": data_manager.eeg_id,
                    "numPhases": len(edited_phases),
                    "patientId": data_manager.patient_id,
                    "phases": [
                        {
                            "location": phase["location"],
                            "goalIntensity": phase.get("goalIntensity", 0),
                            "pulseParameters": {
                                "phase": "MONO" if phase["pulseMode"] == "Monophasic" else "BIPHASIC"
                            },
                            "frequency": phase["frequency"],
                            "burstDuration": 0,
                            "burstFrequency": 0,
                            "burstNumber": 0,
                            "interBurstInterval": 0,
                            "interTrainInterval": phase["interTrainInterval"],
                            "phaseDuration": phase.get("phaseDuration", 0),
                            "trainDuration": phase["trainDuration"],
                            "trainNumber": phase["trainNumber"],
                        }
                        for phase in edited_phases
                    ],
                    "subtype": "CORTICAL",
                    "totalDuration": 0,
                    "type": "TREATMENT",
                }

                asyncio.run(data_manager.reject_protocol(rejection_reason, protocol))
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
    st.markdown(f"**Second Review Date:** {analysis_meta['secondReviewDatetime'] or 'N/A'}")