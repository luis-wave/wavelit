import asyncio
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from services.mert2_data_management.mert_api import MeRTApi
import pandas as pd
import uuid

def parse_eeg_data_extended(data):
    rows = []
    for key, content in data.items():
        recording_date = content.get('baseProtocol', {}).get('recordingDate', None)
        frequency = content.get('baseProtocol', {}).get('frequency', None)
        rows.append({
            'EEGId': key,
            'RecordingDate': recording_date,
            "BaseProtocol": frequency
        })

    # Create the DataFrame
    df = pd.DataFrame(rows)

    # Convert 'RecordingDate' to datetime for proper sorting
    df['RecordingDate'] = pd.to_datetime(df['RecordingDate'], errors='coerce')

    # Sort the DataFrame by 'RecordingDate' in descending order
    df = df.sort_values(by='RecordingDate', ascending=False)

    return df

# Asynchronous function to fetch all the required data and store it in session state
async def load_data():
    api = MeRTApi(
        patient_id="PAT-7ab945ce-b879-11ed-b74f-0273bda7c1f3",
        eeg_id="EEG-3ed32f89-0d11-40c2-909d-12cdfacd9cab",
        clinic_id="c3e85638-86c9-11eb-84b6-0aea104587df"
    )

    await api._login()

    if "eeg_info" not in st.session_state:
        st.session_state.eeg_info = await api.get_user()

    if "user_profile" not in st.session_state:
        st.session_state.user_profile = await api.get_user_profile(
            user_id="STF-e465eb68-ba87-11eb-8611-06b700432873",
            user_group_id="a9cf82fc-7c4d-11eb-b3ca-0a508de74e57",
        )

    if "patient_data" not in st.session_state:
        st.session_state.patient_data = await api.fetch_patient_by_id()

    if "fetch_all_eeg_data" not in st.session_state:
        st.session_state.fetch_all_eeg_data = await api.fetch_all_eeg_info_by_patient_id()


    if "clinic_info" not in st.session_state:
        st.session_state.clinic_info = await api.fetch_clinic_info()

    if "eeg_history" not in st.session_state:
        st.session_state.eeg_history = await api.fetch_all_eeg_info_by_patient_id()

    if "treatment_count" not in st.session_state:
        st.session_state.treatment_count = await api.get_completed_treatment_count_by_patient_id()

    if "eeg_reports" not in st.session_state:
        st.session_state.eeg_reports = await api.get_eeg_report()


    # if "neuroref_report" not in st.session_state:
    #     st.session_state.neuroref_report = await api.get_neuroref_report(
    #         eeg_ids=parse_eeg_data_extended(st.session_state.fetch_all_eeg_data)['EEGId'].values.tolist()
    #     )

    # if "neuroref_cz_report" not in st.session_state:
    #     st.session_state.neuroref_cz_report = await api.get_neuroref_cz_report(
    #         eeg_ids=parse_eeg_data_extended(st.session_state.fetch_all_eeg_data)['EEGId'].values.tolist()
    #     )

    neuroref_linked_ear_report_ids = list(st.session_state.eeg_reports['neuroRefReports'].keys())
    #neuroref_centroid_report_ids = list(st.session_state.eeg_reports['neuroRefReports'].keys())


    if neuroref_linked_ear_report_ids:
        neuro_le_reports = []
        for report_id in neuroref_linked_ear_report_ids:
            response = await api.download_neuroref_report(report_id=report_id)
            neuro_le_reports.append(response)
        st.session_state.downloaded_neuroref_report = neuro_le_reports

    # if neuroref_centroid_report_ids:
    #     neuro_cz_reports = []

    #     for report_id in neuroref_centroid_report_ids:
    #         if "downloaded_neuroref_cz_report" not in st.session_state:
    #             response  = await api.download_neuroref_cz_report(report_id=report_id)
    #             neuro_cz_reports.append(response)

    #         st.session_state.downloaded_neuroref_cz_report = neuro_cz_reports



async def update_data(eeg_ids):
    api = MeRTApi(
        patient_id="PAT-7ab945ce-b879-11ed-b74f-0273bda7c1f3",
        eeg_id="EEG-3ed32f89-0d11-40c2-909d-12cdfacd9cab",
        clinic_id="c3e85638-86c9-11eb-84b6-0aea104587df"
    )

    await api._login()

    st.session_state.neuroref_report = await api.get_neuroref_report(
        eeg_ids=eeg_ids
    )

    st.session_state.downloaded_neuroref_report  = await api.download_neuroref_report(report_id=st.session_state.neuroref_report["reportId"])

    st.session_state.neuroref_cz_report = await api.get_neuroref_cz_report(
        eeg_ids=eeg_ids
    )

    st.session_state.downloaded_neuroref_cz_report  = await api.download_neuroref_cz_report(report_id=st.session_state.neuroref_cz_report["reportId"])







# Call async function to load data into session state
asyncio.run(load_data())

# Extract data from session state to display in the Streamlit UI
patient_data = st.session_state.patient_data
clinic_info = st.session_state.clinic_info

# Start rendering the UI
st.title("NeuroSynchrony Review")

eeg_id = "EEG-133abaab-eef5-4e5e-8aa7-c86ac2b54dda"
col1, col2 = st.columns(2)

with col1:
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
    st.subheader(st.session_state.clinic_info["name"])
    st.markdown(f"ClinicId: **{clinic_info['clinicId']}**")
    st.markdown(f"Phone number: **{clinic_info['phone']}**")
    st.markdown(f"City: **{clinic_info['address']['city']}**")
    st.markdown(f"State: **{clinic_info['address']['state']}**")
    st.markdown(f"Country: **{clinic_info['address']['country']}**")

with col2:
    eeg_history = st.session_state.eeg_history
    eeg_history_df = parse_eeg_data_extended(eeg_history)
    eeg_history_df['include?'] = True

    st.header("EEG History")
    with st.form("data_editor_form", border=False):
        edited_eeg_history_df = st.data_editor(eeg_history_df, hide_index=True)
        # Submit button for the form
        submitted = st.form_submit_button("Update Report")
        if submitted:
            st.json(edited_eeg_history_df.to_json())

            approved_eegs = edited_eeg_history_df[edited_eeg_history_df['include?']==True]
            asyncio.run(update_data(approved_eegs['EEGId'].values.tolist()))
            pdf_viewer(st.session_state.downloaded_neuroref_report , height=700)
        else:
            if "downloaded_neuroref_report" in st.session_state:
                for idx, report in enumerate(st.session_state.downloaded_neuroref_report):
                    with st.expander(label=f"Neurosynchrony - Linked Ears {idx}"):
                        pdf_viewer(report, height=700, key = f'linked_ears {idx}')

            if "downloaded_neuroref_cz_report" in st.session_state:
                for report in st.session_state.downloaded_neuroref_cz_report:
                    with st.expander(label=f"Neurosynchrony - Cetroid {idx}", key = uuid.uuid4()):
                        pdf_viewer(report, height=700, key = f'centroid {idx}')

    subcol1, subcol2 = st.columns(2)

    with subcol1:
        st.button("Accept", type="primary")
    with subcol2:
        st.button("Reject")
