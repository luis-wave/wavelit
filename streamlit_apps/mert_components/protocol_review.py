import ast
import os
import asyncio
import numpy as np
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit_shadcn_ui as ui
import streamlit.components.v1 as components
from utils.helpers import calculate_age, format_datetime
from utils.performance_cache import (
    get_protocol_defaults_optimized, 
    get_eeg_info_cached,
    get_doctor_approval_state_cached,
    validate_phase_change,
    performance_monitor
)
from .review_utils import EEGReviewState, mert2_user
from mywaveanalytics.pipelines import ngboost_protocol_pipeline
from graphs import fft_plot_ngboost


SIGMA_PROTOCOLS_MINI_URL = os.getenv("SIGMA_PROTOCOLS_MINI_URL")


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
    st.title("Protocol Reviews")

    patient_data = st.session_state.patient_data
    clinic_info = st.session_state.clinic_info

    first_name = patient_data["profileInfo"]["name"]["first"]
    last_name = patient_data["profileInfo"]["name"]["last"]
    middle_name = patient_data["profileInfo"]["name"]["middle"]
    username = patient_data["profileInfo"]["username"]
    dob = patient_data["profileInfo"]["dateOfBirth"]
    age = calculate_age(dob)
    sex = patient_data["profileInfo"]["sex"].capitalize()
    patient_id = patient_data["profileInfo"]["patientId"]
    primary_complaint = patient_data.get("clinicalInfo", {}).get("primaryComplaint", "-")
    is_having_seizures = (
        "Yes" if patient_data["clinicalInfo"]["isHavingSeizures"] else "No"
    )

    if "CORTICAL" in st.session_state.treatment_count:
        treatment_count = st.session_state.treatment_count["CORTICAL"]
    else:
        treatment_count = 0

    # Fetch EEG info using cached version
    eeg_info = get_eeg_info_cached(data_manager.patient_id, data_manager.eeg_id, data_manager.clinic_id)
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

    # Fetch doctor approval state using cached version
    doctor_approval_state = get_doctor_approval_state_cached(data_manager.patient_id, data_manager.eeg_id, data_manager.clinic_id)

    col1, col2 = st.columns(2)

    with col1:
        patient_data = st.session_state.patient_data
        clinic_info = st.session_state.clinic_info

        first_name = patient_data["profileInfo"]["name"]["first"]
        last_name = patient_data["profileInfo"]["name"]["last"]
        middle_name = patient_data["profileInfo"]["name"]["middle"]
        dob = patient_data["profileInfo"]["dateOfBirth"]
        age = calculate_age(dob)
        patient_id = patient_data["profileInfo"]["patientId"]
        primary_complaint = patient_data.get("clinicalInfo", {}).get("primaryComplaint", "Not Provided")

        is_having_seizures = (
            "Yes" if patient_data["clinicalInfo"]["isHavingSeizures"] else "No"
        )

        if "CORTICAL" in st.session_state.treatment_count:
            treatment_count = st.session_state.treatment_count["CORTICAL"]
        else:
            treatment_count = 0

        with ui.card(key="protocol_patient_card"):
            # Patient Name
            ui.element("h2",
                    children=[f"{first_name} {middle_name + ' ' if middle_name else ''}{last_name}"],
                    className="text-2xl font-bold mb-4",
                    key="name")

            ui.element("hr", className="my-4", key="divider1")
            # Demographics
            ui.element("span", children=["Age"], className="text-gray-500 text-sm font-medium", key="dob_label")
            ui.element("div", children=[f"{age} years old"], className="mb-2", key="dob_value2")

            ui.element("span", children=["Treatment Sessions"], className="text-gray-500 text-sm font-medium", key="sessions_label")
            ui.element("div", children=[str(treatment_count)], className="mb-4", key="sessions_value")

            # Seizure Status
            if is_having_seizures == "Yes":
                ui.element("div",
                        children=["⚠️ Active Seizure History"],
                        className="bg-red-100 text-red-700 p-2 rounded mb-4",
                        key="seizure_status"
                        )

            # Primary Complaint
            ui.element("h3", children=["Primary Complaint"], className="text-lg font-medium mb-2", key="complaint_header")
            ui.element("div",
                    children=[primary_complaint],
                    className="bg-gray-50 p-3 rounded mb-4",
                    key="complaint_value"
                    )

            ui.element("hr", className="my-4", key="divider2")

            # Clinic Information
            ui.element("h3", children=[clinic_info["name"]], className="text-lg font-medium mb-2", key="clinic_name")

            ui.element("span", children=["Clinic ID"], className="text-gray-500 text-sm font-medium", key="clinic_id_label")
            ui.element("div", children=[clinic_info['clinicId']], className="mb-2", key="clinic_id_value")

            ui.element("span", children=["Patient ID"], className="text-gray-500 text-sm font-medium", key="patient_id_label")
            ui.element("div", children=[data_manager.patient_id], className="mb-2", key="eeg_id_value")

            ui.element("span", children=["EEG ID"], className="text-gray-500 text-sm font-medium", key="eeg_id_label")
            ui.element("div", children=[eeg_info_data['eegId']], className="mb-2", key="eeg_id_value")

            # Review Status
            ui.element("hr", className="my-4", key="divider1")
            analysis_meta = eeg_info["eegInfo"]["analysisMeta"]

            current_state = (
                EEGReviewState[analysis_meta["reviewState"]]
                if analysis_meta["reviewState"]
                else EEGReviewState.PENDING
            )

            current_state_name = current_state.name.replace('_', ' ')

            ui.element("h3", children=["EEG Review Status"], className="text-xl font-bold mb-4", key="header_title")

            if current_state_name != 'REJECTED':
                ui.element("div", children=[f"Status: {current_state_name}"],
                        className="bg-blue-500 text-white px-4 py-2 rounded-full inline-block mb-6", key="header_status")
            else:
                ui.element("div", children=[f"Status: {current_state_name}"],
                    className="bg-red-500 text-white px-4 py-2 rounded-full inline-block mb-6", key="header_status")

    with col2:
        base = SIGMA_PROTOCOLS_MINI_URL+f"?Patient-Id-1={patient_id}"
        html = f'<iframe src="{base}" frameborder="0" width="100%" height="400px"></iframe>'
        st.components.v1.html(html, height=400, scrolling=False)


    protocol_col1, protocol_col2 = st.columns(2)

    with protocol_col1:

        preset_phases={}
        delivered_phases=None
        # Create multiple protocol phase tables
        if protocol_data and "phases" in protocol_data:
            delivered_phases = protocol_data["phases"]
            n_phases = len(protocol_data["phases"])
            presets = get_protocol_defaults_optimized(n_phases, data_manager.patient_id, data_manager.eeg_id, data_manager.clinic_id)

            if presets and "phases" in presets:
                preset_phases = presets["phases"]
                phases = map_preset_to_phases(preset_phases)
        else:
            # Determine initial phase count based on primary complaint
            initial_phases = 2 if primary_complaint == "Autism Spectrum Disorder" else 1
            presets = get_protocol_defaults_optimized(initial_phases, data_manager.patient_id, data_manager.eeg_id, data_manager.clinic_id)

            if presets and "phases" in presets:
                preset_phases = presets["phases"]
                phases = map_preset_to_phases(preset_phases)
            protocol_data = {"phases": phases}

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



        st.header("Protocol")

        if not delivered_phases:
            base_protocol["location"] = None
            base_protocol["pulseMode"] = None
            delivered_phases = [base_protocol]

        for i, phase_dict in enumerate(delivered_phases):
            if "pulseParameters" in phase_dict:
                raw_phase = phase_dict["pulseParameters"].get("phase", "BIPHASIC")

                if raw_phase:
                    # If it contains "MONO", classify as "Monophasic", else "Biphasic"
                    if "MONO" in raw_phase.upper():
                        phase_dict["pulseMode"] = "Monophasic"
                    else:
                        phase_dict["pulseMode"] = "Biphasic"
                else:
                    phase_dict["pulseMode"] = "Biphasic"
            else:
                # Default to Biphasic if pulseParameters missing
                phase_dict["pulseMode"] = None

            #n_submitted_protocols = len(protocol_data["phases"])

            # # If the
            # if n_submitted_protocols > 1:
            #     if i < n_submitted_protocols:
            #         phase_dict["frequency"] = protocol_data["phases"][i]["frequency"]


        # Convert phase to DataFrame
        phase_df = pd.DataFrame(delivered_phases)

        phase_df.insert(0, "Phase", phase_df.index + 1)

        visible_columns = [
            "Phase",
            "frequency",
            "interTrainInterval",
            "location",
            "phaseDuration",
            "trainDuration",
            "trainNumber",
            "pulseMode",
        ]

        # Create editable table for each phase - Added unique key
        edited_df = st.data_editor(
            phase_df,
            disabled=True,
            num_rows="fixed",
            use_container_width=True,
            key=f"phase_display",  # Added unique key based on phase index
            column_order=visible_columns,
            column_config={
                "pulseMode": st.column_config.SelectboxColumn(
                    "Pulse Mode", options=["Biphasic", "Monophasic"], required=True
                ),
                "location": st.column_config.SelectboxColumn(
                    "Location", options=location_options, required=True
                ),
                "frequency": st.column_config.NumberColumn(
                    "Frequency (Hz)", min_value=0.1, max_value=100, step=0.01
                ),
                "trainDuration": st.column_config.NumberColumn(
                    "Train Duration (s)", min_value=1, step=0.1
                ),
                "trainNumber": st.column_config.NumberColumn(
                    "Train Number", min_value=1, step=1
                ),
                "interTrainInterval": st.column_config.NumberColumn(
                    "Inter-Train Interval (s)", min_value=1, step=0.1
                ),
            },
            hide_index=True,
        )


    with protocol_col2:

        st.header("Phase Editor")

        phase_button_col1, phase_button_col2 = st.columns(2)



        # Initialize phase count if not exists
        if "phase_count" not in st.session_state:
            if protocol_data and "phases" in protocol_data:
                st.session_state["phase_count"] = len(protocol_data["phases"])
            elif primary_complaint == "Autism Spectrum Disorder":
                st.session_state["phase_count"] = 2
            else:
                st.session_state["phase_count"] = 1

        # Only fetch defaults when phase count actually changes
        current_phase_count = st.session_state["phase_count"]
        
        if "last_phase_count" not in st.session_state or st.session_state["last_phase_count"] != current_phase_count:
            with st.spinner(f"Loading defaults for {current_phase_count} phases..."):
                presets = get_protocol_defaults_optimized(current_phase_count, data_manager.patient_id, data_manager.eeg_id, data_manager.clinic_id)
                
                if presets and "phases" in presets:
                    preset_phases = presets["phases"]
                    st.session_state["phases"] = map_preset_to_phases(preset_phases)
                    st.session_state["last_phase_count"] = current_phase_count

        with phase_button_col1:
            if st.session_state["phase_count"] < 4:
                if st.button("Add Phase", key="add_phase_button"):
                    new_count = st.session_state["phase_count"] + 1
                    is_valid, message = validate_phase_change(st.session_state["phase_count"], new_count)
                    
                    if is_valid:
                        st.session_state["phase_count"] = new_count
                        st.rerun()
                    else:
                        st.warning(message)
            else:
                st.write("Cannot add more than three phases.")

        with phase_button_col2:
            if st.session_state["phase_count"] > 1:
                if st.button("Remove Phase", key="remove_phase_button"):
                    new_count = st.session_state["phase_count"] - 1
                    is_valid, message = validate_phase_change(st.session_state["phase_count"], new_count)
                    
                    if is_valid:
                        st.session_state["phase_count"] = new_count
                        st.rerun()
                    else:
                        st.warning(message)
            else:
                st.write("Need at least one phase for protocol.")




        if "phases" in st.session_state:
            phases = st.session_state["phases"]

        for i, phase_dict in enumerate(phases):
            if "pulseParameters" in phase_dict:
                raw_phase = phase_dict["pulseParameters"].get("phase", "BIPHASIC")

                if raw_phase:
                    # If it contains "MONO", classify as "Monophasic", else "Biphasic"
                    if "MONO" in raw_phase.upper():
                        phase_dict["pulseMode"] = "Monophasic"
                    else:
                        phase_dict["pulseMode"] = "Biphasic"
                else:
                    phase_dict["pulseMode"] = "Biphasic"
            else:
                # Default to Biphasic if pulseParameters missing
                phase_dict["pulseMode"] = "Biphasic"

            #n_submitted_protocols = len(protocol_data["phases"])

            # # If the
            # if n_submitted_protocols > 1:
            #     if i < n_submitted_protocols:
            #         phase_dict["frequency"] = protocol_data["phases"][i]["frequency"]


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
                        "Frequency (Hz)", min_value=0.1, max_value=100, step=0.001
                    ),
                    "trainDuration": st.column_config.NumberColumn(
                        "Train Duration (s)", min_value=1, step=0.1
                    ),
                    "trainNumber": st.column_config.NumberColumn(
                        "Train Number", min_value=1, step=1
                    ),
                    "interTrainInterval": st.column_config.NumberColumn(
                        "Inter-Train Interval (s)", min_value=1, step=0.1
                    ),
                },
                hide_index=True,
            )

            # Validate that only existing columns are checked
            existing_columns = [col for col in visible_columns if col in edited_df.columns]


            save_phases = st.form_submit_button("Save protocol")

            if save_phases:
                # Validate that no visible column has null values
                if edited_df[existing_columns].isnull().any().any():
                    st.error("Error: One or more required fields contain null values. Please fill all fields before saving.")
                else:
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
                                phase_dict[param] = 0

                            # Ensure NaN values are explicitly converted to None
                            if pd.isna(phase_dict[param]):
                                phase_dict[param] = None

                        # these field(s) are added programmatically in MeRT 2
                        phase_dict["phaseDuration"] = 0
                        phase_dict["goalIntensity"] = 0

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

                        st.success("Protocol updated successfully!")
                        st.rerun()
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


    PROTOCOL_FFT_ONLY = os.getenv("PROTOCOL_FFT_ONLY")
    pid = st.session_state["pid"]
    base = PROTOCOL_FFT_ONLY+f"?c_protocol_Patient-Id-1={pid}"
    html = f'<iframe src="{base}" frameborder="0" width="100%" height="1000px"></iframe>'
    components.html(html, height=1000, scrolling=False)





