"""
Landing page for EEG report review and approval workflow.
"""

import streamlit as st

from services.mert2_data_management.mert_api import MeRTApi

api = MeRTApi()

mert_user_id = st.session_state.id


response = api.get_user_profile(
    user_id=mert_user_id,
    user_group_id="a9cf82fc-7c4d-11eb-b3ca-0a508de74e57",
)

mert2_username = response["username"]

response = api.mert_login(login=True, username=mert2_username)

response = api.fetch_patient_by_id(
    patient_id="PAT-a8a60536-f913-11ee-a83b-0ae5ce097cd9",
    user_group_id="42b1e3cc-e0ec-11eb-ad0d-06f5bfd05d85",
)

clinic_info = response["clinicalInfo"]
primary_complaint = clinic_info["primaryComplaint"]
total_sessions_delivered = clinic_info["totalSessions"]


profile_info = response["profileInfo"]
date_of_birth = profile_info["dateOfBirth"]
sex = profile_info["sex"]
username = profile_info["username"]
patient_id = profile_info["patientId"]
clinic_id = profile_info["clinicId"]

if not profile_info["name"]["middle"]:
    name = profile_info["name"]["first"] + " " + profile_info["name"]["last"]
else:
    name = (
        profile_info["name"]["first"]
        + " "
        + profile_info["name"]["middle"]
        + " "
        + profile_info["name"]["last"]
    )

clinic_info = api.fetch_clinic_info(user_group_id=clinic_id)

clinic_name = clinic_info["name"]
clinic_phone = clinic_info["phone"]
clinic_coordinates = clinic_info["mapCoordinates"]

neuroref_response = api.get_neuroref_report(
    eeg_id="EEG-d2498c3b-e26d-442f-833d-14767a12669e",
    patient_id="PAT-a8a60536-f913-11ee-a83b-0ae5ce097cd9",
    eeg_ids=[
        "EEG-6e57ba2b-c4cc-40d6-bd2e-d33e4a66147b",
        "EEG-95d22cd0-eab4-4bed-aae3-378269b56832",
        "EEG-aa680e40-b207-43c8-8f8d-2d9a726719ad",
        "EEG-d2498c3b-e26d-442f-833d-14767a12669e",
        "EEG-e7359c27-7db4-4550-9560-33d2f0e53861",
        "EEG-fa753c03-4c10-4a1f-aa09-47d6c26c9d28",
        "EEG-ff95e481-6d22-4c77-abd6-79f251c65e40",
    ],
    user_group_id=clinic_id,
)

report_id = neuroref_response["reportId"]
report_type = neuroref_response["type"]
report_name = neuroref_response["name"]
report_approved_state = neuroref_response["approved"]


response = api.download_neuroref_report(
    eeg_id="EEG-d2498c3b-e26d-442f-833d-14767a12669e",
    patient_id="PAT-a8a60536-f913-11ee-a83b-0ae5ce097cd9",
    report_id=report_id,
    user_group_id=clinic_id,
)

st.write(response['title'])

html_content = response['body']
st.markdown(html_content, unsafe_allow_html=True)