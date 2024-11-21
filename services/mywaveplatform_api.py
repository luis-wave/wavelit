import asyncio
import base64
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
import streamlit as st


class MyWavePlatformApi:
    """
    A service class for handling API requests related to EEG data management on MyWave platform.
    """

    def __init__(self, base_url=None, username=None, password=None, api_key=None):
        self.base_url = base_url or os.getenv("BASE_URL")
        self.username = username or os.getenv("CLINICAL_USERNAME")
        self.password = password or os.getenv("CLINICAL_PASSWORD")
        self.api_key = api_key or os.getenv("CLINICAL_API_KEY")

    def get_basic_auth_header(self):
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        auth_header = {"Authorization": f"Basic {encoded_credentials}"}

        if self.api_key:
            auth_header["x-api-key"] = self.api_key

        return auth_header

    async def login(self):
        auth_header = self.get_basic_auth_header()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/user/login",
                headers={**auth_header, "Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    bearer_token = response_data["message"]["IdToken"]
                    return {
                        "Authorization": f"Bearer {bearer_token}",
                        "x-api-key": self.api_key,
                    }
                else:
                    raise Exception("Login failed: " + await response.text())

    async def download_eeg_file(self, eeg_id, headers):
        try:
            request_data = {"eeg_id": eeg_id}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/eeg", headers=headers, json=request_data
                ) as response:
                    response.raise_for_status()

                    download_url = (await response.json()).get("download_url")
                    if download_url:
                        async with session.get(download_url) as file_response:
                            file_response.raise_for_status()

                            parsed_url = urlparse(download_url)
                            file_name = os.path.basename(parsed_url.path)
                            file_extension = Path(file_name).suffix

                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=file_extension
                            ) as tmp_file:
                                tmp_file.write(await file_response.read())
                                return tmp_file.name, file_extension
                    else:
                        st.error("Download URL not found in the response.")
                        return None, None
        except aiohttp.ClientError as e:
            st.error(f"Error downloading EEG file: {e}")
            return None, None

    async def get_heart_rate_variables(self, eeg_id, headers):
        try:
            request_data = {"eeg_id": eeg_id}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/eeg/hr_variables",
                    headers=headers,
                    json=request_data,
                ) as response:
                    response.raise_for_status()

                    ecg_statistics = (await response.json()).get("ecg_statistics", {})
                    heart_rate = ecg_statistics.get("heartrate_bpm")
                    stdev_bpm = ecg_statistics.get("stdev_bpm")

                    st.session_state.heart_rate = heart_rate
                    st.session_state.heart_rate_std_dev = stdev_bpm


                    return heart_rate, stdev_bpm
        except aiohttp.ClientError as e:
            st.error(f"Error retrieving heart rate variables: {e}")
            return None, None

    async def get_aea_onsets(self, eeg_id, headers):
        try:
            request_data = {"eeg_id": eeg_id}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/abnormality/aea",
                    headers=headers,
                    json=request_data,
                ) as response:
                    response.raise_for_status()

                    aea = await response.json()
                    return aea
        except aiohttp.ClientError as e:
            st.error(f"Error retrieving AEA onsets: {e}")
            return None

    async def get_ahr_onsets(self, eeg_id, headers):
        try:
            request_data = {"eeg_id": eeg_id}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/abnormality/ahr",
                    headers=headers,
                    json=request_data,
                ) as response:
                    response.raise_for_status()

                    ahr = await response.json()
                    return ahr
        except aiohttp.ClientError as e:
            st.error(f"Error retrieving AHR onsets: {e}")
            return None

    async def get_autoreject_annots(self, eeg_id, headers):
        try:
            request_data = {"eeg_id": eeg_id}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/abnormality/autoreject",
                    headers=headers,
                    json=request_data,
                ) as response:
                    response.raise_for_status()

                    autoreject = await response.json()
                    return autoreject
        except aiohttp.ClientError as e:
            st.error(f"Error retrieving autoreject annotations: {e}")
            return None


async def fetch_all_data(api, eeg_id, headers):
    tasks = [
        api.download_eeg_file(eeg_id, headers),
        api.get_heart_rate_variables(eeg_id, headers),
        api.get_aea_onsets(eeg_id, headers),
        api.get_ahr_onsets(eeg_id, headers),
        api.get_autoreject_annots(eeg_id, headers),
    ]
    results = await asyncio.gather(*tasks)
    return results
