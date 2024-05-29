import os
import base64
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import time


import requests
import streamlit as st

class MyWavePlatformApi:
    """
    A service class for handling API requests related to EEG data management on MyWave platform.
    """

    def __init__(self, base_url=None, username=None, password=None, api_key=None):
        self.base_url = base_url or os.getenv("BASE_URL")
        self.username = username or os.getenv("USERNAME")
        self.password = password or os.getenv("PASSWORD")
        self.api_key = api_key or os.getenv("API_KEY")

    def get_basic_auth_header(self):
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        auth_header = {"Authorization": f"Basic {encoded_credentials}"}

        if self.api_key:
            auth_header["x-api-key"] = self.api_key

        return auth_header

    def login(self):
        auth_header = self.get_basic_auth_header()
        response = requests.post(f"{self.base_url}/user/login", headers=auth_header)

        if response.status_code == 200:
            bearer_token = response.json()["message"]["IdToken"]
            return {
                "Authorization": f"Bearer {bearer_token}",
                "x-api-key": self.api_key,
            }
        else:
            raise Exception("Login failed: " + response.text)

    def download_eeg_file(self, eeg_id, headers):
        try:
            request_data = {"eeg_id": eeg_id}
            response = requests.get(f"{self.base_url}/eeg", headers=headers, json=request_data)
            st.success(response.json())
            response.raise_for_status()
            time.sleep(1)


            download_url = response.json().get("download_url")
            if download_url:
                response = requests.get(download_url)
                response.raise_for_status()

                parsed_url = urlparse(download_url)
                file_name = os.path.basename(parsed_url.path)
                file_extension = Path(file_name).suffix

                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                    tmp_file.write(response.content)
                    return tmp_file.name, file_extension
            else:
                st.error("Download URL not found in the response.")
                return None, None
        except requests.exceptions.RequestException as e:
            st.error(f"Error downloading EEG file: {e}")
            return None, None

    def get_heart_rate_variables(self, eeg_id, headers):
        """
        Retrieves heart rate and standard deviation from the specified endpoint.

        :param eeg_id: The ID of the EEG data (str)
        :param headers: Headers for the API request (dict)
        :return: Tuple (heart rate, standard deviation) or (None, None)
        """
        try:
            request_data = {"eeg_id": eeg_id}
            response = requests.get(f"{self.base_url}/eeg/hr_variables", headers=headers, json=request_data)
            response.raise_for_status()

            ecg_statistics = response.json().get("ecg_statistics", {})
            heart_rate = ecg_statistics.get("heartrate_bpm")
            stdev_bpm = ecg_statistics.get("stdev_bpm")

            return heart_rate, stdev_bpm
        except requests.exceptions.RequestException as e:
            st.error(f"Error retrieving heart rate variables: {e}")
            return None, None