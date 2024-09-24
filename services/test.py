"""
Load MeRT 2 data into session for Streamlit visualization.
"""

import asyncio

import streamlit as st
from mert2_data_management.mert_api import MeRTApi


async def main():
    api = MeRTApi()
    await api._login()
    eeg_info = await api.get_user()
    user_profile = await api.get_user_profile(
        user_id="STF-e465eb68-ba87-11eb-8611-06b700432873",
        user_group_id="a9cf82fc-7c4d-11eb-b3ca-0a508de74e57",
    )
    patient_data = await api.fetch_patient_by_id(
        patient_id="PAT-015ea160-75d3-11ef-8661-0268b37b7f5f",
        user_group_id="da39a264-c60b-11ee-b40a-02fe5dd0030f",
    )
    ref = await api.download_neuroref_report(
        eeg_id="EEG-133abaab-eef5-4e5e-8aa7-c86ac2b54dda",
        patient_id="PAT-015ea160-75d3-11ef-8661-0268b37b7f5f",
        report_id="e74332e4-8a19-481e-a257-cdef875d54b3",
        user_group_id="da39a264-c60b-11ee-b40a-02fe5dd0030f",
    )

    print(ref[:1000])


asyncio.run(main())
