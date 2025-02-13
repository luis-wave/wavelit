import ast
import asyncio
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit_shadcn_ui as ui


from .review_utils import EEGReviewState, mert2_user

def map_preset_to_phases(preset_phases):
    mapping = {
        "frequency": "frequency",
        "location": "location",
        "pulse_phase": "pulseParameters",
        "burst_duration": "burstDuration",
        "burst_frequency": "burstFrequency",
        "burst_number": "burstNumber",
        "inter_train_interval": "interTrainInterval",
        "inter_burst_interval": "interBurstInterval",
        "train_duration": "trainDuration",
        "train_number": "trainNumber"
    }

    mapped_phases = []
    for phase in preset_phases:
        mapped_phase = {
            mapping[key]: value for key, value in phase.items() if key in mapping
        }
        # Handling nested pulseParameters
        if "pulse_phase" in phase:
            mapped_phase["pulseParameters"] = {"phase": phase["pulse_phase"]}

        mapped_phases.append(mapped_phase)

    return mapped_phases





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

        if ("approvedByName" in protocol_data) and  ("isRejected" not in protocol_data):
            approver_name = protocol_data["approvedByName"]
            st.markdown(f"**Approved by:** {approver_name}")

        if "isRejected" in protocol_data:
            st.markdown("**Protocol is REJECTED**")

        if "isRejected" not in protocol_data and ("approvedByName" not in protocol_data) :
            st.markdown("**Protocol is PENDING**")
    else:
        protocol_data = None

    # Fetch doctor approval state
    doctor_approval_state = asyncio.run(data_manager.get_doctor_approval_state())



    # Display metadata
    # Card for displaying metadata
    with ui.card(key="metadata_card"):
        # EEG ID
        ui.element("span", children=["EEG ID"], className="text-gray-400 text-sm font-medium m-1", key="eeg_id_label")
        ui.element("div", children=[f"{eeg_info_data['eegId']}"], className="text-base font-semibold m-1", key="eeg_id_value")

        # Patient ID
        ui.element("span", children=["Patient ID"], className="text-gray-400 text-sm font-medium m-1", key="patient_id_label")
        ui.element("div", children=[f"{data_manager.patient_id}"], className="text-base font-semibold m-1", key="patient_id_value")

        # Clinic ID
        ui.element("span", children=["Clinic ID"], className="text-gray-400 text-sm font-medium m-1", key="clinic_id_label")
        ui.element("div", children=[f"{data_manager.clinic_id}"], className="text-base font-semibold m-1", key="clinic_id_value")

        # Recording Date
        ui.element("span", children=["Recording Date"], className="text-gray-400 text-sm font-medium m-1", key="recording_date_label")
        ui.element("div", children=[f"{base_protocol['recordingDate']}"], className="text-base font-semibold m-1", key="recording_date_value")



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

    preset_phases={}
    # Create multiple protocol phase tables
    if protocol_data and "phases" in protocol_data:
        phases = protocol_data["phases"]

        n_phases = len(protocol_data["phases"])

        presets = asyncio.run(data_manager.get_protocol_review_default_values(n_phases=n_phases))

        if presets and "phases" in presets:
            preset_phases = presets["phases"]
            phases = map_preset_to_phases(preset_phases)
    else:
        # If no protocol data, create a single phase from base protocol
        # base_protocol["pulseMode"] = base_protocol.get("pulseMode", "Biphasic")
        # base_protocol["location"] = base_protocol.get("location", "F1-FZ-F2")
        # phases = [base_protocol]
        presets = asyncio.run(data_manager.get_protocol_review_default_values(n_phases=1))

        if presets and "phases" in presets:
            preset_phases = presets["phases"]
            phases = map_preset_to_phases(preset_phases)
        protocol_data = {"phases": phases}

    # Add a button to add new phase
    if st.button("Add Phase", key="add_phase_button"):
        current_n_phases = len(phases)
        try:
            presets = asyncio.run(data_manager.get_protocol_review_default_values(n_phases=current_n_phases+1))

            if presets and "phases" in presets:
                preset_phases = presets["phases"]
                st.session_state["phases"] = map_preset_to_phases(preset_phases)

        except Exception as e:
            st.error(f"Failed to add new phase: {str(e)}")

    if "phases" in st.session_state:
        phases = st.session_state["phases"]

        for i, phase_dict in enumerate(protocol_data["phases"]):
            phases[i] = phase_dict


    if len(protocol_data["phases"]) > 1:
        for i, phase_dict in enumerate(protocol_data["phases"]):
            phases[i] = phase_dict

    for i, phase_dict in enumerate(phases):
        if "pulseParameters" in phase_dict:
            raw_phase = phase_dict["pulseParameters"].get("phase", "BIPHASIC")
            # If it contains "MONO", classify as "Monophasic", else "Biphasic"
            if "MONO" in raw_phase.upper():
                phase_dict["pulseMode"] = "Monophasic"
            else:
                phase_dict["pulseMode"] = "Biphasic"
        else:
            # Default to Biphasic if pulseParameters missing
            phase_dict["pulseMode"] = "Biphasic"

        n_submitted_protocols = len(protocol_data["phases"])

        # If the
        if n_submitted_protocols > 1:
            if i < n_submitted_protocols:
                phase_dict["frequency"] = protocol_data["phases"][i]["frequency"]


    # Convert phase to DataFrame
    phase_df = pd.DataFrame(phases)

    phase_df.insert(0, "Phase", phase_df.index + 1)

    phase_df["include"] = True

    visible_columns = [
        "Phase",
        "frequency",
        "interTrainInterval",
        "location",
        "phaseDuration",
        "trainDuration",
        "trainNumber",
        "pulseMode",
        "include"
    ]


    with st.form("additional_phases_form"):

        # Create editable table for each phase - Added unique key
        edited_df = st.data_editor(
            phase_df,
            num_rows="fixed",
            use_container_width=True,
            key=f"phase_editor",  # Added unique key based on phase index
            disabled=["recordingDate"] if "recordingDate" in phase_df.columns else [],
            column_order=visible_columns,
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

        edited_df = edited_df[edited_df["include"]].reset_index(drop=True)

        edited_df = edited_df[edited_df["include"]].reset_index(drop=True).drop(columns=["include"])

        save_phases = st.form_submit_button("Save protocol")

    if save_phases:
        # Convert the edited DataFrame back to a list of dicts
        edited_phases = edited_df.to_dict(orient="records")

        for idx,  phase_dict in enumerate(edited_phases):
            phase_dict.pop("Phase", None)
            if phase_dict["pulseMode"] == "Monophasic":
                phase_dict["pulseMode"] = "MONO"
            elif phase_dict["pulseMode"] == "Biphasic":
                phase_dict["pulseMode"] = "BIPHASIC"

            for param in  ("burstDuration", "burstFrequency", "burstNumber", "interBurstInterval"):
                if phase_dict[param] == 0:
                    phase_dict[param] = None

                # Ensure NaN values are explicitly converted to None
                if pd.isna(phase_dict[param]):
                    phase_dict[param] = None

            phase_dict["pulseParameters"] = ast.literal_eval(phase_dict["pulseParameters"])

            if phase_dict["pulseMode"] == "MONO":
                phase_dict["pulseParameters"]["phase"] = "MONO"
            elif phase_dict["pulseMode"] == "BIPHASIC":
                phase_dict["pulseParameters"]["phase"] = "BIPHASIC"



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
                "phases": edited_phases,
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
                    state=EEGReviewState.COMPLETED.name,
                )
            )
            st.success("Protocol updated successfully!")
        except Exception as e:
            st.error(f"Failed to update protocol: {str(e)}")

    # Create a separate form for actions
    with st.form("protocol_actions_form"):
        rejection_reason = st.text_input("Rejection Reason", key="rejection_reason_input")
        reject_submitted = st.form_submit_button("Reject Protocol")

    # Handle form submissions

    if reject_submitted:
        if rejection_reason:
            try:
                # Convert the edited DataFrame back to a list of dicts
                edited_phases = edited_df.to_dict(orient="records")

                for idx,  phase_dict in enumerate(edited_phases):
                    phase_dict.pop("Phase", None)
                    if phase_dict["pulseMode"] == "Monophasic":
                        phase_dict["pulseMode"] = "MONO"
                    elif phase_dict["pulseMode"] == "Biphasic":
                        phase_dict["pulseMode"] = "BIPHASIC"

                    for param in  ("burstDuration", "burstFrequency", "burstNumber", "interBurstInterval"):
                        if phase_dict[param] == 0:
                            phase_dict[param] = None

                        # Ensure NaN values are explicitly converted to None
                        if pd.isna(phase_dict[param]):
                            phase_dict[param] = None

                    phase_dict["pulseParameters"] = ast.literal_eval(phase_dict["pulseParameters"])

                    if phase_dict["pulseMode"] == "MONO":
                        phase_dict["pulseParameters"]["phase"] = "MONO"
                    elif phase_dict["pulseMode"] == "BIPHASIC":
                        phase_dict["pulseParameters"]["phase"] = "BIPHASIC"

                protocol = {
                    "acknowledgeState": {"clinician": "", "physician": ""},
                    "approvedByName": "",
                    "approvedDate": "",
                    "createdByName": "",
                    "createdDate": "",
                    "eegId": data_manager.eeg_id,
                    "numPhases": len(edited_phases),
                    "patientId": data_manager.patient_id,
                    "phases": edited_phases,
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
