import asyncio
import os
import traceback

import streamlit as st
import toml

from services.auth import authenticate_user
from services.eeg_data_manager import EEGDataManager


# Function to read version from pyproject.toml
def get_version_from_pyproject():
    try:
        pyproject_data = toml.load("pyproject.toml")
        return pyproject_data["tool"]["poetry"]["version"]
    except Exception as e:
        st.error(f"Error reading version from pyproject.toml: {e}")
        return "Unknown"


def authorize_user_access():
    name, authentication_status, username, authenticator = authenticate_user()

    if authentication_status:
        authenticator.logout("Logout", "sidebar")
        st.write(f"Welcome *{name}*")

    elif authentication_status is False:
        st.error("Username/password is incorrect")
    elif authentication_status is None:
        st.warning("Please enter your username and password")

    return name


async def access_eeg_data(eeg_id=None):

    base_url = os.getenv("BASE_URL")

    if eeg_id:
        if eeg_id.startswith("EEG-"):
            username = os.getenv("CLINICAL_USERNAME")
            password = os.getenv("CLINICAL_PASSWORD")
            api_key = os.getenv("CLINICAL_API_KEY")
        else:
            username = os.getenv("CONSUMER_USERNAME")
            password = os.getenv("CONSUMER_PASSWORD")
            api_key = os.getenv("CONSUMER_API_KEY")

    eeg_manager = EEGDataManager(base_url, username, password, api_key)
    await eeg_manager.initialize()

    if not eeg_id:
        # Upload EEG file
        uploaded_file = st.file_uploader("Upload an EEG file", type=["dat", "edf"])

        if uploaded_file is not None:
            try:
                await eeg_manager.handle_uploaded_file(uploaded_file)
            except Exception as e:
                tb_exception = traceback.TracebackException.from_exception(e)
                st.error(
                    f"File upload or processing failed: {''.join(tb_exception.format())}"
                )
        # Download EEG file by EEG ID
        st.write("Or")
        eeg_id = st.text_input("Enter EEG ID")
        if st.button("Download EEG Data"):
            with st.spinner("Downloading EEG data..."):
                try:
                    await eeg_manager.handle_downloaded_file(eeg_id)
                    await eeg_manager.fetch_additional_data(eeg_id)
                except Exception as e:
                    tb_exception = traceback.TracebackException.from_exception(e)
                    st.error(
                        f"Data retrieval or processing failed: {''.join(tb_exception.format())}"
                    )
    else:
        try:
            await eeg_manager.handle_downloaded_file(eeg_id)
            await eeg_manager.fetch_additional_data(eeg_id)
        except Exception as e:
            tb_exception = traceback.TracebackException.from_exception(e)
            st.error(
                f"Data retrieval or processing failed: {''.join(tb_exception.format())}"
            )
