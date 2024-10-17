from mert_api import MeRTApi

api = MeRTApi()
response = api.fetch_eeg_info_by_patient_id_and_eeg_id(
    patient_id="PAT-18e57ca8-3020-11ef-be2e-0258c0e3d6e9",
    eeg_id="EEG-13ef882f-a4bd-46c8-b117-c2488747241d",
    user_group_id="c904a43e-2f2f-11ef-ab69-06ebeb04c94d",
)
# print(response)
# print(response)


# print(api.mert_login(login=True, username="wn_vatech_test1"))


response = api.fetch_patient_by_id(
    patient_id="PAT-5e8a7244-ba80-11ec-8346-02703ed3d209",
    user_group_id="0c8ebfe2-6cbd-11ec-bed9-028d6822ed3f",
)


response = api.get_report_approval_state(
    patient_id="PAT-18e57ca8-3020-11ef-be2e-0258c0e3d6e9",
    eeg_id="EEG-13ef882f-a4bd-46c8-b117-c2488747241d",
    user_group_id="c904a43e-2f2f-11ef-ab69-06ebeb04c94d",
)
print(response)
