import asyncio
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from services.mert2_data_management.mert_data_manager import MeRTDataManager

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
            with st.expander(label=f"Neurosynchrony - Linked Ears {idx}"):
                pdf_viewer(report, height=700, key=f'linked_ears {idx}')
                delete_button = st.button(label="Delete Report", key=f'linked_ears {idx} button')

                if delete_button:
                    asyncio.run(data_manager.delete_neuroref_report(report_id=report_id))
                    st.rerun()

    if "downloaded_neuroref_cz_report" in st.session_state:
        for idx, report_data in enumerate(st.session_state.downloaded_neuroref_cz_report):
            report, report_id = report_data
            with st.expander(label=f"Neurosynchrony - Centroid {idx}"):
                pdf_viewer(report, height=700, key=f'centroid {idx}')
                delete_button = st.button(label="Delete Report", key=f'centroid {idx} button')

                if delete_button:
                    asyncio.run(data_manager.delete_neuroref_cz_report(report_id=report_id))
                    st.rerun()

    st.subheader("Documents")
    with st.popover("Add documents", use_container_width=True):
        uploaded_zip = st.file_uploader("Upload a Persyst report", type="pdf")

    st.subheader("Artifact Distortions")
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

    st.subheader("Add Irregularity")
    with st.popover("Add irregularities", use_container_width=True):
        with st.form("add_irregularity_form", border=False):
            options = st.multiselect(
                "Select irregularity",
                [
                    "Irregular EEG Activity",
                    "Irregular Heart Rhythm",
                    "Other"
                ]
            )
            other_input = None
            if "Other" in options:
                other_input = st.text_input("Please specify other irregularity:")

            submit_button = st.form_submit_button(label="Submit")

            if submit_button:
                irregularities = options + ([other_input] if other_input else [])
                asyncio.run(data_manager.save_artifact_distortions(irregularities))
                st.success("Irregularities saved successfully!")