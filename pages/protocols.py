import base64
import json
import os

import pandas as pd  # Import pandas library
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit_authenticator as stauth

# Define your configuration variables
BASE_URL = os.getenv("BASE_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
API_KEY = os.getenv("API_KEY")

import yaml
from yaml.loader import SafeLoader

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
                    **auth_header,
                    "Authorization": f"Bearer {bearer_token}",
                }
            else:
                raise Exception("Login failed: " + response.text)

    # Function to build URL for API endpoints
    def build_url(base_url, graph_type):
        return f"{base_url}/graphs/{graph_type}"

    # Function to fetch data from an API Gateway endpoint using authenticated GET requests
    def perform_get_request(url, request_data, headers):
        response = requests.get(url, headers=headers, json=request_data)
        response.raise_for_status()
        return response.json()

    # Function to get EEG IDs by patient ID
    def get_eeg_ids_by_patient_id(base_url, patient_id, headers):
        url = f"{base_url}/eeg/all-by-patientid?patient_id={patient_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    # Streamlit App
    st.title("Wave Neuro Platform Protocol Viewer")

    # Input for Patient ID inside a borderless form
    with st.form(key='patient_id_form'):
        patient_id = st.text_input("Enter Patient ID")
        submit_button = st.form_submit_button(label='Get EEG IDs by Patient ID')

    if submit_button and patient_id:
        try:
            # Step 1: Authenticate and get headers
            auth_manager = AuthManager(BASE_URL, USERNAME, PASSWORD, API_KEY)
            auth_headers = auth_manager.login()

            # Step 2: Fetch EEG IDs by Patient ID
            eeg_ids_data = get_eeg_ids_by_patient_id(BASE_URL, patient_id, auth_headers)

            # Display the list of EEG IDs
            eeg_ids = eeg_ids_data.get('body', [])
            if eeg_ids:
                st.write("EEG IDs for the given Patient ID:")
                eeg_ids_df = pd.DataFrame(eeg_ids, columns=["EEG ID"])
                st.dataframe(eeg_ids_df)

                all_posterior_data = []
                all_protocol_frequencies = []
                all_recording_dates = []

                # Fetch and display protocol data for each EEG ID
                for eeg_id in eeg_ids:
                    st.write(f"Fetching data for EEG ID: {eeg_id}")
                    try:
                        # Build URL for magnitude spectra
                        magnitude_spectra_endpoint = build_url(BASE_URL, "magnitude_spectra")
                        request_data = {"eeg_id": eeg_id}
                        magnitude_spectra_data = perform_get_request(magnitude_spectra_endpoint, request_data, auth_headers)
                        posterior = magnitude_spectra_data.get('posterior')
                        freqs = magnitude_spectra_data.get('freqs')

                        # Build URL for cortical protocol
                        cortical_protocol_endpoint = BASE_URL + "/protocols/cortical"
                        cortical_protocol_data = perform_get_request(cortical_protocol_endpoint, request_data, auth_headers)
                        protocol = cortical_protocol_data.get('protocol')
                        protocol_frequency = protocol.get('frequency') if protocol else None
                        recording_date = protocol.get('recording_date') if protocol else None

                        if posterior and freqs and protocol_frequency is not None:
                            st.success(f"Data fetched successfully for EEG ID: {eeg_id}")

                            # Collect data for plotting
                            all_posterior_data.append((posterior, freqs, eeg_id))
                            all_protocol_frequencies.append(protocol_frequency)
                            all_recording_dates.append((recording_date, eeg_id))
                        else:
                            st.error(f"Invalid data received from API for EEG ID: {eeg_id}.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error fetching data for EEG ID {eeg_id}: {e}")
                    except Exception as e:
                        st.error(f"Authentication Error for EEG ID {eeg_id}: {e}")

                # Sort by recording date
                all_recording_dates.sort()

                # Create a dataframe with EEG ID, recording date, and protocol frequency
                protocol_df = pd.DataFrame({
                    "EEG ID": [eeg_id for _, eeg_id in all_recording_dates],
                    "Recording Date": [recording_date for recording_date, _ in all_recording_dates],
                    "Protocol Frequency": [all_protocol_frequencies[i] for i in range(len(all_protocol_frequencies))]
                })

                st.write("EEG ID, Recording Date, and Protocol Frequency:")
                st.dataframe(protocol_df)

                # Plot all data in a single graph
                fig = go.Figure()

                for (posterior, freqs, eeg_id), (recording_date, _) in zip(all_posterior_data, all_recording_dates):
                    fig.add_trace(go.Scatter(x=freqs, y=posterior, mode='lines', name=f'{eeg_id} ({recording_date})'))

                # Highlight the protocol frequency of the latest recording date
                latest_protocol_freq = protocol_df.iloc[-1]["Protocol Frequency"]
                latest_recording_date = protocol_df.iloc[-1]["Recording Date"]
                latest_eeg_id = protocol_df.iloc[-1]["EEG ID"]

                fig.add_vline(x=latest_protocol_freq, line=dict(color='red', dash='dash'),
                              annotation_text=f"Current Protocol: {round(latest_protocol_freq, 1)} Hz ({latest_recording_date})",
                              annotation_position="top left")

                fig.update_layout(
                    title=f"Posterior Magnitude Spectra for all EEG IDs",
                    xaxis_title="Frequency (Hz)",
                    yaxis_title="Magnitude Spectra (µV)",
                    template="plotly_white",
                    width=1200,
                    height=800
                )
                st.plotly_chart(fig)
            else:
                st.error("No EEG IDs found for the given Patient ID.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching data: {e}")
        except Exception as e:
            st.error(f"Authentication Error: {e}")

elif st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None:
    st.warning("Please enter your username and password")
