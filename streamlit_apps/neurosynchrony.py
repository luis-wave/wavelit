import asyncio
import pandas as pd
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from services.mert2_data_management.mert_data_manager import MeRTDataManager
from enum import Enum
import streamlit.components.v1 as components
from access_control import access_eeg_data

from streamlit_dashboards import (ecg_visualization_dashboard,
                                  eeg_visualization_dashboard)

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


mert2_user = {
    "STF-e465eb68-ba87-11eb-8611-06b700432873": "Luis Camargo",
    "STF-6d38ac86-ba89-11eb-8b42-029e69ddbc8b": "Alex Ring",
    "STF-ac677ad4-a595-11ec-82d9-02fd9bf033d7": "Stephanie Llaga",
    "STF-e8b6c0a2-27f5-11ed-b837-02b0e344b06f": "Patrick Polk",
    "STF-934d6632-a17e-11ec-b364-0aa26dca46cb": "Joseph Chong",
    "STF-031845e2-b505-11ec-8b5d-0a86265d54df": "Nicole Yu",
    "STF-d844feb2-241c-11ef-8e46-02fb253d52c7": "Binh Le",
    "STF-7a0aa2d4-241c-11ef-a5ac-06026d518b71": "Rey Mendoza",
    "STF-0710bc38-2e40-11ed-a807-027d8017651d": "Jay Kumar",
    "STF-472808de-ba89-11eb-967d-029e69ddbc8b": "Jijeong Kim",
    "STF-143c1a12-8657-11ef-8e6a-020ab1ebdc67": "Uma Gokhale",
    "STF-8b4db98a-8657-11ef-9d8b-020ab1ebdc67": "Uma Gokhale2"
}


tabs = ["Reports", "Protocols", "EEG"]

tab1, tab2, tab3 = st.tabs(tabs)

class EEGReviewState(Enum):
    PENDING = 0
    FIRST_REVIEW = 1
    SECOND_REVIEW_NEEDED = 2
    SECOND_REVIEW = 3
    CLINIC_REVIEW = 4
    COMPLETED = 6
    REJECTED = 7

REJECTION_REASONS = {
    "possibleDrowsiness": "Possible Drowsiness",
    "excessiveArtifact": "Excessive Artifact",
    "poorEegSetup": "Poor EEG Setup",
    "incorrectUpload": "Incorrect Upload",
    "other": "Other"
}

def get_next_state(current_state: EEGReviewState) -> EEGReviewState:
    state_order = [
        EEGReviewState.PENDING,
        EEGReviewState.FIRST_REVIEW,
        EEGReviewState.SECOND_REVIEW_NEEDED,
        EEGReviewState.SECOND_REVIEW,
        EEGReviewState.COMPLETED
    ]
    try:
        current_index = state_order.index(current_state)
        return state_order[current_index + 1] if current_index < len(state_order) - 1 else current_state
    except ValueError:
        return current_state

@st.fragment
def render_eeg_review(data_manager):
    st.markdown("## EEG Review")

    # Fetch EEG info
    eeg_info = asyncio.run(data_manager.fetch_eeg_info_by_patient_id_and_eeg_id())
    analysis_meta = eeg_info['eegInfo']['analysisMeta']

    current_state = EEGReviewState[analysis_meta['reviewState']] if analysis_meta['reviewState'] else EEGReviewState.PENDING

    if analysis_meta and 'reviewerStaffId' in analysis_meta:
        first_reviewer = mert2_user.get(analysis_meta['reviewerStaffId'], 'N/A')
    else:
        first_reviewer = 'N/A'

    if analysis_meta and 'secondReviewerStaffId' in analysis_meta:
        second_reviewer = mert2_user.get(analysis_meta['secondReviewerStaffId'], 'N/A')
    else:
        second_reviewer = 'N/A'

    if current_state == EEGReviewState.REJECTED:
        st.markdown("### Rejected")
        st.markdown(f"**Review Date:** {analysis_meta['rejectionDatetime']}")
        st.markdown(f"**Rejected by:** {mert2_user[analysis_meta['rejectionReviewerStaffId']]}")
        st.markdown("**Rejection Reason(s):**")
        for i in analysis_meta["rejectionReason"]:
            st.write(REJECTION_REASONS[i])
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### First Review")
            st.markdown(f"**Review Date:** {analysis_meta['reviewDatetime'] or 'Not reviewed yet'}")
            st.markdown(f"**Approved By:** {first_reviewer}")

        with col2:
            st.markdown("### Second Review")
            st.markdown(f"**Review Date:** {analysis_meta['secondReviewDatetime'] or 'Not reviewed yet'}")
            st.markdown(f"**Approved By:** {second_reviewer}")

    st.markdown(f"**Current State:** {current_state.name}")

    # Check if the current user can perform a review
    can_review = st.session_state['id'] not in [analysis_meta['reviewerStaffId'], analysis_meta['secondReviewerStaffId']]

    if can_review:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Proceed Review"):
                next_state = get_next_state(current_state)
                try:
                    result = asyncio.run(data_manager.update_eeg_review(
                        is_first_reviewer=(current_state == EEGReviewState.PENDING),
                        state=next_state.name
                    ))
                    st.success(f"Review updated to {next_state.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update review: {str(e)}")

        with col2:
            with st.form(key='reject_form'):
                st.markdown("### Reject Review")
                rejection_reasons = st.multiselect(
                    "Select Rejection Reasons",
                    options=list(REJECTION_REASONS.keys()),
                    format_func=lambda x: REJECTION_REASONS[x]
                )
                reject_button = st.form_submit_button(label="Reject Review")

                if reject_button:
                    if not rejection_reasons:
                        st.error("Please select at least one rejection reason.")
                    else:
                        try:
                            result = asyncio.run(data_manager.update_eeg_review(
                                is_first_reviewer=(current_state == EEGReviewState.PENDING),
                                state=EEGReviewState.REJECTED.name,
                                rejection_reason=rejection_reasons
                            ))
                            st.success("Review rejected.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to reject review: {str(e)}")

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
        "powerlineInterference": "Powerline interference"
    }

def translate_artifact_name(artifact_name):
    artifact_map = get_artifact_map()
    return artifact_map.get(artifact_name, artifact_name.capitalize())

@st.fragment
def render_artifact_distortions(data_manager):
    st.subheader("Artifact Distortions")

    if 'eeg_reports' in st.session_state and 'artifacts' in st.session_state.eeg_reports:
        artifacts = st.session_state.eeg_reports['artifacts']
        if artifacts:
            st.write("Existing Artifacts:")
            for artifact_id, artifact_info in artifacts.items():
                full_label = translate_artifact_name(artifact_info['name'])
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

    with st.popover("Add artifacts", use_container_width=True):
        with st.form("add_artifact_form", border=False):
            artifact_map = get_artifact_map()
            reverse_artifact_map = {v: k for k, v in artifact_map.items()}

            options = st.multiselect(
                "Add artifact distortion",
                list(artifact_map.values()) + ["Other"]
            )
            other_input = None
            if "Other" in options:
                other_input = st.text_input("Please specify other artifact:")

            submit_button = st.form_submit_button(label="Submit")

            if submit_button:
                artifacts = [reverse_artifact_map.get(option, option) for option in options if option != "Other"]
                if other_input:
                    artifacts.append(other_input)
                asyncio.run(data_manager.save_artifact_distortions(artifacts))
                st.success("Artifacts saved successfully!")
                st.rerun()

@st.fragment
def render_abnormalities(data_manager):
    st.subheader("Abnormalities")

    converter = {
        "Irregular EEG Activity (AEA)": "aea",
        "Irregular Heart Rhythm (AHR)": "ahr"
    }
    reverse_converter = {v: k for k, v in converter.items()}

    if 'eeg_reports' in st.session_state and 'abnormalities' in st.session_state.eeg_reports:
        abnormalities = st.session_state.eeg_reports['abnormalities']
        if abnormalities:
            st.write("Existing Abnormalities:")
            for abnormality_id, abnormality in abnormalities.items():
                name = reverse_converter.get(abnormality['name'], abnormality['name'].upper())
                status = "Approved" if abnormality['isApproved'] else "Not Approved"

                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"- {name}: {status}")
                with col2:
                    if not abnormality['isApproved']:
                        if st.button("Approve", key=f"approve_{abnormality_id}"):
                            asyncio.run(data_manager.approve_abnormality(abnormality_id))
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

    with st.popover("Add irregularities", use_container_width=True):
        with st.form("add_irregularity_form", border=False):
            options = st.multiselect(
                "Select irregularity",
                list(converter.keys()) + ["Other"]
            )
            other_input = None
            if "Other" in options:
                other_input = st.text_input("Please specify other irregularity:")

            submit_button = st.form_submit_button(label="Add")

            if submit_button:
                converted_options = [converter.get(option, option) for option in options if option != "Other"]
                if other_input:
                    converted_options.append(other_input)

                asyncio.run(data_manager.save_abnormalities(converted_options))
                st.success("Irregularities added successfully!")
                st.rerun()

@st.fragment
def render_documents(data_manager):
    st.subheader("Documents")

    if 'eeg_reports' in st.session_state and 'documents' in st.session_state.eeg_reports:
        documents = st.session_state.eeg_reports['documents']
        if documents:
            st.write("Existing Documents:")
            for doc_id, doc_info in documents.items():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"- {doc_info['filename']}")
                with col2:
                    try:
                        document_content = asyncio.run(data_manager.download_document(doc_id))
                        st.download_button(
                            label=f"Download",
                            data=document_content,
                            file_name=doc_info['filename'],
                        )
                    except Exception as e:
                        st.error(f"Failed to download {doc_info['filename']}. Please try again.")
                with col3:
                    if st.button(f"Delete", key=f"delete_{doc_id}"):
                        try:
                            asyncio.run(data_manager.delete_document(doc_id))
                            st.success(f"Document {doc_info['filename']} deleted successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete {doc_info['filename']}. Please try again.{e}")
        else:
            st.write("No existing documents found.")
    else:
        st.write("No document data available.")

    with st.popover("Add documents", use_container_width=True):
        uploaded_file = st.file_uploader("Upload a Persyst report", type="pdf")

        if uploaded_file is not None:
            if st.button("Submit Document"):
                try:
                    document_id = asyncio.run(data_manager.save_document(uploaded_file))
                    st.success(f"Document uploaded successfully! Document ID: {document_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to upload document. Error: {str(e)}")


def delete_report(data_manager, report_id, ref='default'):
    if ref == 'default':
        asyncio.run(data_manager.delete_neuroref_report(report_id))
        st.success(f"Neuroref {report_id} successfully deleted!")
        st.rerun()
    elif ref=='cz':
        asyncio.run(data_manager.delete_neuroref_cz_report(report_id))
        st.success(f"Neuroref Cz {report_id} successfully deleted!")
        st.rerun()

@st.fragment
def render_protocol_page(data_manager):
    st.title("EEG Protocol")

    # Fetch EEG info
    eeg_info = asyncio.run(data_manager.fetch_eeg_info_by_patient_id_and_eeg_id())
    base_protocol = eeg_info['baseProtocol']
    analysis_meta = eeg_info['eegInfo']['analysisMeta']
    eeg_info_data = eeg_info['eegInfo']

    # Fetch doctor approval state
    doctor_approval_state = asyncio.run(data_manager.get_doctor_approval_state())

    if analysis_meta and 'reviewerStaffId' in analysis_meta:
        first_reviewer = mert2_user.get(analysis_meta['reviewerStaffId'], 'N/A')
    else:
        first_reviewer = 'N/A'

    if analysis_meta and 'secondReviewerStaffId' in analysis_meta:
        second_reviewer = mert2_user.get(analysis_meta['secondReviewerStaffId'], 'N/A')
    else:
        second_reviewer = 'N/A'

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
        st.markdown(f"Name: {doctor_approval_state['clinician']['firstName'] or 'N/A'} {doctor_approval_state['clinician']['lastName'] or 'N/A'}")
    with col2:
        st.markdown("**Physician**")
        st.markdown(f"Approved: {doctor_approval_state['physician']['approved']}")
        st.markdown(f"Date: {doctor_approval_state['physician']['datetime'] or 'N/A'}")
        st.markdown(f"Name: {doctor_approval_state['physician']['firstName'] or 'N/A'} {doctor_approval_state['physician']['lastName'] or 'N/A'}")

    # Create editable dataframe for base protocol
    st.subheader("Base Protocol")

    # Add new fields to the protocol
    base_protocol['pulseMode'] = base_protocol.get('pulseMode', 'Biphasic')
    base_protocol['location'] = base_protocol.get('location', 'F1-FZ-F2')

    # Create the dataframe without transposing
    protocol_df = pd.DataFrame([base_protocol])

    # Define the location options
    location_options = [
        "FP1-FPZ-FP2", "F1-FZ-F2", "C1-CZ-C2", "P1-PZ-P2", "F1-F3-F5", "F2-F4-F6",
        "F7-FT7-T3", "F8-FT8-T4", "CP1-CPZ-CP2", "FC1-FCZ-FC2", "TP7-T3-FT7",
        "TP8-T4-FT8", "C5-C3-C1", "C6-C4-C2", "C3-CP3-P3", "C4-CP4-P4", "P3-CP5-T3",
        "P4-CP6-T4", "P1-P3-P5", "P2-P4-P6", "P3-P5-P7", "P4-P6-P8", "P3-PO3-O1",
        "P4-PO4-O2", "PO3-O1-PO7", "PO4-O2-PO8"
    ]

    with st.form("protocol_data_editor_form", border=False):
        # Create the editable dataframe
        edited_df = st.data_editor(
            protocol_df,
            num_rows="fixed",
            use_container_width=True,
            column_config={
                "pulseMode": st.column_config.SelectboxColumn(
                    "Pulse Mode",
                    options=['Biphasic', 'Monophasic'],
                    required=True
                ),
                "location": st.column_config.SelectboxColumn(
                    "Location",
                    options=location_options,
                    required=True
                )
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
                            "clinician":doctor_approval_state['clinician'],
                            "physician": doctor_approval_state['physician']
                        },
                        "approvedByName": "",
                        "approvedDate": "",
                        "createdByName": "UAT Scientist",
                        "createdDate": datetime.utcnow().isoformat() + "Z",
                        "eegId": data_manager.eeg_id,
                        "numPhases": 1,
                        "patientId": data_manager.patient_id,
                        "phases": [{
                            "location": updated_protocol["location"],
                            "goalIntensity": updated_protocol.get("goalIntensity", 0),
                            "pulseParameters": {"phase": "MONO" if updated_protocol["pulseMode"] == "Monophasic" else "BIPHASIC"},
                            "frequency": updated_protocol["frequency"],
                            "burstDuration": updated_protocol.get("burstDuration"),
                            "burstFrequency": updated_protocol.get("burstFrequency"),
                            "burstNumber": updated_protocol.get("burstNumber"),
                            "interBurstInterval": updated_protocol.get("interBurstInterval"),
                            "interTrainInterval": updated_protocol["interTrainInterval"],
                            "phaseDuration": updated_protocol.get("phaseDuration", 0),
                            "trainDuration": updated_protocol["trainDuration"],
                            "trainNumber": updated_protocol["trainNumber"]
                        }],
                        "subtype": "CORTICAL",
                        "totalDuration": updated_protocol.get("totalDuration", 0),
                        "type": "TREATMENT"
                    }

                    # Call the save_protocol method
                    result = asyncio.run(data_manager.save_protocol(protocol))
                    st.success("Protocol updated successfully!")
                except Exception as e:
                    st.error(f"Failed to update protocol: {str(e)}")

        with col2:
            rejection_reason = st.text_input("Rejection Reason")
            if st.form_submit_button("Reject Protocol"):
                if rejection_reason:
                    try:
                        # Prepare the protocol object (same as in the save function)
                        protocol = {
                            # ... (same as in the save function)
                        }

                        # Call the reject_protocol method
                        result = asyncio.run(data_manager.reject_protocol(rejection_reason, protocol))
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


@st.fragment
def render_notes(data_manager, eeg_scientist_patient_notes):
    st.subheader("EEG Scientist Patient Notes")

    # Form for adding a new note
    with st.form("new_note_form"):
        st.write("Add New Note")
        recording_date = st.date_input("Recording Date")
        subject = st.text_input("Subject")
        content = st.text_area("Content")
        submitted = st.form_submit_button("Submit Note")

        if submitted:
            new_note = {
                "recordingDate": recording_date.strftime("%a, %B %d %Y"),
                "subject": subject,
                "content": content
            }
            try:
                asyncio.run(data_manager.save_eeg_scientist_patient_note(new_note))
                st.success("Note added successfully!")
                st.rerun()  # Rerun the app to refresh the notes list
            except Exception as e:
                st.error(f"Failed to add note: {str(e)}")

    st.divider()

    if not eeg_scientist_patient_notes:
        st.write("No notes available.")
        return

    # Sort notes by date (newest first)
    sorted_notes = sorted(eeg_scientist_patient_notes.items(), key=lambda x: x[0], reverse=True)

    for date, note in sorted_notes:
        st.markdown(f"### {note['subject']} - {note['recordingDate']}")
        st.write(f"**Date Edited:** {note['dateEdited']}")
        st.write(f"**Recording Date:** {note['recordingDate']}")
        st.write(f"**Subject:** {note['subject']}")
        st.write("**Content:**")

        # Display content in a text area
        st.text_area("", value=note['content'], height=150, key=f"note_{date}", disabled=True)

        st.divider()


if ('eegid' in st.session_state) and ('pid' in st.session_state) and ('clinicid' in st.session_state):
    # Initialize MeRTDataManager
    data_manager = MeRTDataManager(
        patient_id = st.session_state['pid'],
        eeg_id = st.session_state['eegid'],
        clinic_id = st.session_state['clinicid']
    )


# Load all data into session state
asyncio.run(data_manager.load_all_data())

with tab1:

    # Start rendering the UI
    st.title("NeuroSynchrony Review")

    col1, col2 = st.columns(2)

    with col1:
        patient_data = st.session_state.patient_data
        clinic_info = st.session_state.clinic_info

        first_name = patient_data["profileInfo"]["name"]["first"]
        last_name = patient_data["profileInfo"]["name"]["last"]
        middle_name = patient_data["profileInfo"]["name"]["middle"]
        username = patient_data["profileInfo"]["username"]
        dob = patient_data["profileInfo"]["dateOfBirth"]
        sex = patient_data["profileInfo"]["sex"].capitalize()
        patient_id = patient_data["profileInfo"]["patientId"]
        primary_complaint = patient_data["clinicalInfo"]["primaryComplaint"]
        is_having_seizures = "Yes" if patient_data["clinicalInfo"]["isHavingSeizures"] else "No"

        if 'CORTICAL' in st.session_state.treatment_count:
            treatment_count = st.session_state.treatment_count['CORTICAL']
        else:
            treatment_count = 0

        # Display patient data
        st.header(f"{first_name} {middle_name + ' ' if middle_name else ''}{last_name}")
        st.markdown(f"Username: **{username}**")
        st.markdown(f"Sex: **{sex}**")
        st.markdown(f"DOB: **{dob}**")
        st.markdown(f"Seizure History: **{is_having_seizures}**")
        st.markdown(f"Treatment Session Count: **{treatment_count}**")
        st.markdown(f"PatientId: **{patient_id}**")
        st.markdown(f"Primary Chief Complaint: **{primary_complaint}**")

        st.divider()

        # Clinic info
        st.subheader(clinic_info["name"])
        st.markdown(f"ClinicId: **{clinic_info['clinicId']}**")
        st.markdown(f"Phone number: **{clinic_info['phone']}**")
        st.markdown(f"City: **{clinic_info['address']['city']}**")
        st.markdown(f"State: **{clinic_info['address']['state']}**")
        st.markdown(f"Country: **{clinic_info['address']['country']}**")

    if 'eegScientistPatientNotes' in patient_data:
        eeg_scientist_patient_notes = patient_data['eegScientistPatientNotes']
    else:
        eeg_scientist_patient_notes = None

    render_notes(data_manager, eeg_scientist_patient_notes)

    with col2:
        render_eeg_review(data_manager)
        eeg_history_df = st.session_state.eeg_history

        with st.popover("Generate report"):
            st.header("EEG History")
            with st.form("data_editor_form", border=False):
                edited_eeg_history_df = st.data_editor(eeg_history_df, hide_index=True)
                regenerate_neuroref = st.form_submit_button("Generate Neuroref Report")
                regenerate_neuroref_cz = st.form_submit_button("Generate Neuroref Cz Report")

            if regenerate_neuroref:
                approved_eegs = edited_eeg_history_df[edited_eeg_history_df['include?']==True]
                asyncio.run(data_manager.update_neuroref_reports(approved_eegs['EEGId'].values.tolist()))
                st.rerun()

            if regenerate_neuroref_cz:
                approved_eegs = edited_eeg_history_df[edited_eeg_history_df['include?']==True]
                asyncio.run(data_manager.update_neuroref_cz_reports(approved_eegs['EEGId'].values.tolist()))
                st.rerun()


        st.subheader("Reports")
        if "downloaded_neuroref_report" in st.session_state:
            for idx, report_data in enumerate(st.session_state.downloaded_neuroref_report):
                report, report_id = report_data
                with st.expander(label=f"Neurosynchrony - Linked Ears {report_id}"):
                    pdf_viewer(report, height=700, key=f'linked_ears {idx}')
                    st.download_button(label = "Download Neuroref", data = report, file_name = f"Neurosynchrony-{report_id}.pdf", key=f"download-{report_id}")
                    if st.button(label="Delete", key=f"Neurosynchrony-{report_id}"):
                        delete_report(data_manager, report_id)
                        st.success(f"Neuroref {report_id} successfully deleted!")


        if "downloaded_neuroref_cz_report" in st.session_state:
            for idx, report_data in enumerate(st.session_state.downloaded_neuroref_cz_report):
                report, report_id = report_data
                with st.expander(label=f"Neurosynchrony - Centroid {report_id}"):
                    pdf_viewer(report, height=700, key=f'centroid {idx}')
                    st.download_button(label = "Download Neuroref Cz", data = report, file_name = f"Neurosynchrony-Cz-{report_id}.pdf", key=f"download-cz-{report_id}")
                    if st.button(label="Delete", key=f"Neurosynchrony-cz-{report_id}"):
                        delete_report(data_manager, report_id, ref='cz')
                        st.success(f"Neuroref Cz {report_id} successfully deleted!")


        render_documents(data_manager)

        render_artifact_distortions(data_manager)

        render_abnormalities(data_manager)


with tab2:
    render_protocol_page(data_manager)
    st.title("Protocol Queue")
    html = f'<iframe src="https://app.sigmacomputing.com/embed/1-7DtFiDy0cUmAAIztlEecY5" frameborder="0" width="100%" height="900px"></iframe>'
    components.html(html, height=1000, scrolling=False)

with tab3:
    asyncio.run(access_eeg_data(st.session_state['eegid']))
    eeg_visualization_dashboard()
