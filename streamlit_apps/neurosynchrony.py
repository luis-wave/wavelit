import asyncio
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from services.mert2_data_management.mert_data_manager import MeRTDataManager

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)



def translate_artifact_name(artifact_name):
    artifact_map = {
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
    return artifact_map.get(artifact_name, "Other")



# Render helper functions
def render_artifact_distortions(data_manager):
    st.subheader("Artifact Distortions")

    # Check if eeg_reports exists in session state and has artifacts
    if 'eeg_reports' in st.session_state and 'artifacts' in st.session_state.eeg_reports:
        artifacts = st.session_state.eeg_reports['artifacts']
        if artifacts:
            st.write("Existing Artifacts:")
            for artifact_id, artifact_info in artifacts.items():
                full_label = translate_artifact_name(artifact_info['name'])
                st.write(f"- {full_label}")
        else:
            st.write("No existing artifacts found.")
    else:
        st.write("No artifact data available.")

    with st.popover("Add artifacts", use_container_width=True):
        with st.form("add_artifact_form", border=False):
            options = st.multiselect(
                "Add artifact distortion",
                [
                    "Electrocardiographic interference (ECG)",
                    "Excessive muscle tension (EMG)",
                    "Eye wandering",
                    "Eyeblink artifact (EOG)",
                    "Forehead tension",
                    "Improper ear clip (A1/A2) set-up",
                    "Jaw tension",
                    "Lead wandering",
                    "Movement",
                    "Neck tension",
                    "Possible drowsiness",
                    "Powerline interference",
                    "Other"
                ],
            )
            other_input = None
            if "Other" in options:
                other_input = st.text_input("Please specify other artifact:")

            submit_button = st.form_submit_button(label="Submit")

            if submit_button:
                artifacts = options + ([other_input] if other_input else [])
                asyncio.run(data_manager.save_artifact_distortions(artifacts))
                st.success("Artifacts saved successfully!")
                st.rerun()  # Rerun the app to refresh the artifact list


def render_abnormalities(data_manager):
    st.subheader("Abnormalities")

    # Check if eeg_reports exists in session state and has abnormalities
    if 'eeg_reports' in st.session_state and 'abnormalities' in st.session_state.eeg_reports:
        abnormalities = st.session_state.eeg_reports['abnormalities']
        if abnormalities:
            st.write("Existing Abnormalities:")
            for abnormality in abnormalities.values():
                name = abnormality['name'].upper()
                status = "Approved" if abnormality['isApproved'] else "Not Approved"
                st.write(f"- {name}: {status}")
        else:
            st.write("No existing abnormalities found.")
    else:
        st.write("No abnormality data available.")

    with st.popover("Add irregularities", use_container_width=True):
        with st.form("add_irregularity_form", border=False):
            options = st.multiselect(
                "Select irregularity",
                [
                    "Irregular EEG Activity (AEA)",
                    "Irregular Heart Rhythm (AHR)",
                    "Other"
                ]
            )
            other_input = None
            if "Other" in options:
                other_input = st.text_input("Please specify other irregularity:")

            submit_button = st.form_submit_button(label="Submit")

            if submit_button:
                irregularities = options + ([other_input] if other_input else [])
                asyncio.run(data_manager.save_abnormalities(irregularities))
                st.success("Irregularities saved successfully!")
                st.rerun()  # Rerun the app to refresh the abnormalities list


def render_documents(data_manager):
    st.subheader("Documents")

    # Display existing documents
    if 'eeg_reports' in st.session_state and 'documents' in st.session_state.eeg_reports:
        documents = st.session_state.eeg_reports['documents']
        if documents:
            st.write("Existing Documents:")
            for doc_id, doc_info in documents.items():
                st.write(f"- {doc_info['filename']} (Size: {doc_info['size']} bytes)")

                # Add a download button for each document
                if st.button(f"Download {doc_info['filename']}", key=f"download_{doc_id}"):
                    try:
                        # Assuming you have a method to download the document in your data_manager
                        document_content = asyncio.run(data_manager.download_document(doc_id))
                        st.download_button(
                            label=f"Click to download {doc_info['filename']}",
                            data=document_content,
                            file_name=doc_info['filename'],
                            mime="application/pdf"
                        )
                    except Exception as e:
                        logger.error(f"Error downloading document {doc_id}: {str(e)}")
                        st.error(f"Failed to download {doc_info['filename']}. Please try again.")
        else:
            st.write("No existing documents found.")
    else:
        st.write("No document data available.")

    # Upload new documents
    with st.popover("Add documents", use_container_width=True):
        uploaded_file = st.file_uploader("Upload a Persyst report", type="pdf")

        if uploaded_file is not None:
            if st.button("Submit Document"):
                try:
                    document_id = asyncio.run(data_manager.save_document(uploaded_file))
                    st.success(f"Document uploaded successfully! Document ID: {document_id}")

                    # Refresh the EEG reports to include the new document
                    asyncio.run(data_manager.load_eeg_reports())
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error uploading document: {str(e)}")
                    st.error("Failed to upload document. Please try again.")


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
    eeg_id="EEG-3ed32f89-0d11-40c2-909d-12cdfacd9cab",
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
            submitted = st.form_submit_button("Update Report")
        if submitted:
            st.subheader("Reports")
            approved_eegs = edited_eeg_history_df[edited_eeg_history_df['include?']==True]
            asyncio.run(data_manager.update_neuroref_reports(approved_eegs['EEGId'].values.tolist()))
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