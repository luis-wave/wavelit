import asyncio
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from services.mert2_data_management.mert_data_manager import MeRTDataManager
from enum import Enum

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

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
    "incorrectUpload": "Incorrect Upload"
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

def render_eeg_review(data_manager):
    st.markdown("## EEG Review")

    # Fetch EEG info
    eeg_info = asyncio.run(data_manager.fetch_eeg_info_by_patient_id_and_eeg_id())
    analysis_meta = eeg_info['eegInfo']['analysisMeta']

    current_state = EEGReviewState[analysis_meta['reviewState']] if analysis_meta['reviewState'] else EEGReviewState.PENDING

    if current_state == EEGReviewState.REJECTED:
        st.markdown("### Rejected")
        st.markdown(f"**Review Date:** {analysis_meta['rejectionDatetime']}")
        st.markdown(f"**Reviewer ID:** {analysis_meta['rejectionReviewerStaffId']}")
        st.markdown("**Rejection Reason(s):**")
        for i in analysis_meta["rejectionReason"]:
            st.write(REJECTION_REASONS[i])
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### First Review")
            st.markdown(f"**Review Date:** {analysis_meta['reviewDatetime'] or 'Not reviewed yet'}")
            st.markdown(f"**Reviewer ID:** {analysis_meta['reviewerStaffId'] or 'N/A'}")

        with col2:
            st.markdown("### Second Review")
            st.markdown(f"**Review Date:** {analysis_meta['secondReviewDatetime'] or 'Not reviewed yet'}")
            st.markdown(f"**Reviewer ID:** {analysis_meta['secondReviewerStaffId'] or 'N/A'}")

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



# Initialize MeRTDataManager
data_manager = MeRTDataManager(
    patient_id="PAT-7ab945ce-b879-11ed-b74f-0273bda7c1f3",
    eeg_id="EEG-06bc6524-2fe7-49b8-8c33-860fefec808a",
    clinic_id="c3e85638-86c9-11eb-84b6-0aea104587df"
)

# Load all data into session state
asyncio.run(data_manager.load_all_data())

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
    treatment_count = st.session_state.treatment_count['CORTICAL']

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

with col2:
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

    render_eeg_review(data_manager)