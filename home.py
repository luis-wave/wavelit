import base64
import os
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
import streamlit as st
import streamlit_authenticator as stauth
import toml
import yaml
from mywaveanalytics.libraries import (ecg_statistics,
                                       eeg_computational_library, filters,
                                       mywaveanalytics, references)
from yaml.loader import SafeLoader


# Function to read version from pyproject.toml
def get_version_from_pyproject():
    try:
        pyproject_data = toml.load("pyproject.toml")
        return pyproject_data["tool"]["poetry"]["version"]
    except Exception as e:
        st.error(f"Error reading version from pyproject.toml: {e}")
        return "Unknown"


# Function to calculate EQI
def calculate_eqi(mw_object):
    try:
        mw_copy = mw_object.copy()
        filters.eeg_filter(mw_copy, 1, None)
        filters.notch(mw_copy)
        filters.resample(mw_copy)
        tcp_eeg = references.temporal_central_parasagittal(mw_copy)

        # Artifact ECG signal only before deriving heart rate and heart rate variability measures,
        ecg_events_loc = filters.ecgfilter(mw_copy)

        # Find heart rate
        heart_rate_bpm, heart_rate_std_dev = ecg_statistics.ecg_bpm(ecg_events_loc)
        st.session_state.heart_rate = heart_rate_bpm
        st.session_state.heart_rate_std_dev = heart_rate_std_dev

        eqi_features, z_scored_eqi = eeg_computational_library.calculate_eqi(tcp_eeg)
        eqi_predictions, eqi_score = eeg_computational_library.eqi_svm_inference(
            z_scored_eqi
        )

        return round(eqi_score)
    except Exception as e:
        st.error(f"EEG quality assessment failed for the following reason: {e}")


# Function to load MyWave object
def load_mw_object(path, eegtype):
    try:
        mw_object = mywaveanalytics.MyWaveAnalytics(path, None, None, eegtype)
        return mw_object
    except Exception as e:
        st.error(f"Loading failed for {path}: {e}")
        return None


# Function to save uploaded file
def save_uploaded_file(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(uploaded_file.name).suffix
        ) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Failed to save the uploaded file: {e}")
        return None


# AuthManager Class
class AuthManager:
    def __init__(self, base_url, username, password, api_key=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.api_key = api_key

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


# Function to download EEG file from API
def download_eeg_file(eeg_id, base_url, headers):
    try:
        request_data = {"eeg_id": eeg_id}
        response = requests.get(f"{base_url}/eeg", headers=headers, json=request_data)

        # Debugging: Log request and response
        # st.write(f"Request URL: {base_url}/eeg")
        # st.write(f"Request Headers: {headers}")
        # st.write(f"Request Data: {request_data}")
        # st.write(f"Response Status Code: {response.status_code}")
        # st.write(f"Response Text: {response.text}")

        response.raise_for_status()

        download_url = response.json().get("download_url")
        if download_url:
            response = requests.get(download_url)
            response.raise_for_status()

            # Determine the file type based on the download URL
            parsed_url = urlparse(download_url)
            file_name = os.path.basename(parsed_url.path)
            file_extension = Path(file_name).suffix

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=file_extension
            ) as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name, file_extension
        else:
            st.error("Download URL not found in the response.")
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Error downloading EEG file: {e}")
        return None, None


# Authentication setup
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
    config["pre-authorized"],
)

name, authentication_status, username = authenticator.login()

if st.session_state["authentication_status"]:
    authenticator.logout()
    st.write(f'Welcome *{st.session_state["name"]}*')

    # Initialize Streamlit session state for shared data
    if "mw_object" not in st.session_state:
        st.session_state.mw_object = None

    st.title("EEG Analysis Dashboard")

    st.session_state.heart_rate = None
    st.session_state.heart_rate_std_dev = None

    # Upload EEG file
    uploaded_file = st.file_uploader("Upload an EEG file", type=["dat", "edf"])

    if uploaded_file is not None:
        st.session_state.fname = uploaded_file.name

        # Save uploaded file to disk to make it accessible by file path
        saved_path = save_uploaded_file(uploaded_file)
        if saved_path:
            # Determine EEG type based on file extension
            eeg_type = (
                0
                if uploaded_file.name.lower().endswith(".dat")
                else 10
                if uploaded_file.name.lower().endswith(".edf")
                else None
            )
            if eeg_type is None:
                st.error("Unsupported file type.")
            else:
                mw_object = load_mw_object(saved_path, eeg_type)
                st.success("EEG Data loaded successfully!")

                with st.spinner("Processing..."):
                    st.session_state.mw_object = mw_object.copy()

                    eqi = calculate_eqi(mw_object)

                    # Save the relevant state
                    st.session_state.eqi = eqi

                    st.switch_page("pages/epochs.py")

    # Download EEG file by EEG ID
    st.write("Or")

    eeg_id = st.text_input("Enter EEG ID")
    base_url = os.getenv("BASE_URL")
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    api_key = os.getenv("API_KEY")

    if st.button("Download EEG Data"):
        with st.spinner("Downloading EEG data..."):
            try:
                # Authenticate and get headers with bearer token
                auth_manager = AuthManager(base_url, username, password, api_key)
                headers = auth_manager.login()

                downloaded_path, file_extension = download_eeg_file(
                    eeg_id, base_url, headers
                )
                if downloaded_path:
                    st.success(f"EEG Data for ID {eeg_id} downloaded successfully!")

                    # Determine EEG type based on file extension
                    if file_extension.lower() == ".dat":
                        eeg_type = 0
                    elif file_extension.lower() == ".edf":
                        eeg_type = 10
                    else:
                        st.error("Unsupported file type.")
                        eeg_type = None

                    if eeg_type is not None:
                        mw_object = load_mw_object(downloaded_path, eeg_type)
                        if mw_object:
                            with st.spinner("Loading EEG data..."):
                                st.session_state.mw_object = mw_object.copy()

                                eqi = calculate_eqi(mw_object)

                                # Save the relevant state
                                st.session_state.eqi = eqi

                                st.switch_page("pages/epochs.py")

                        # Clean up downloaded file
                        try:
                            os.remove(downloaded_path)
                        except Exception as e:
                            st.error(f"Failed to delete the temporary file: {e}")
            except Exception as e:
                st.error(f"Authentication or data retrieval failed: {e}")

    # Footer section
    version = get_version_from_pyproject()
    footer_html = f"""
        <div style='position: fixed; bottom: 0; left: 0; padding: 10px;'>
            <span>Version: {version}</span>
        </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

elif st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None:
    st.warning("Please enter your username and password")
