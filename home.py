import os
import streamlit as st
import toml
from services.eeg_data_manager import EEGDataManager
from services.auth import authenticate_user
import traceback

# Function to read version from pyproject.toml
def get_version_from_pyproject():
    try:
        pyproject_data = toml.load("pyproject.toml")
        return pyproject_data["tool"]["poetry"]["version"]
    except Exception as e:
        st.error(f"Error reading version from pyproject.toml: {e}")
        return "Unknown"

def main():
    name, authentication_status, username, authenticator = authenticate_user()

    if authentication_status:
        authenticator.logout("Logout", "main")
        st.write(f'Welcome *{name}*')

        base_url = os.getenv("BASE_URL")
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        api_key = os.getenv("API_KEY")

        eeg_manager = EEGDataManager(base_url, username, password, api_key)

        st.title("EEG Analysis Dashboard")

        # Upload EEG file
        uploaded_file = st.file_uploader("Upload an EEG file", type=["dat", "edf"])

        if uploaded_file is not None:
            eeg_manager.handle_uploaded_file(uploaded_file)

        # Download EEG file by EEG ID
        st.write("Or")
        eeg_id = st.text_input("Enter EEG ID")

        if st.button("Download EEG Data"):
            with st.spinner("Downloading EEG data..."):
                try:
                    eeg_manager.handle_downloaded_file(eeg_id)
                    heart_rate, stdev_bpm = eeg_manager.get_heart_rate_variables(eeg_id)
                    if heart_rate is not None and stdev_bpm is not None:
                        st.session_state.heart_rate = heart_rate
                        st.session_state.heart_rate_std_dev = stdev_bpm
                except Exception as e:
                    tb_exception = traceback.TracebackException.from_exception(e)
                    st.error(f"Authentication or data retrieval failed: {''.join(tb_exception.format())}")

        # Footer section
        version = get_version_from_pyproject()
        footer_html = f"""
            <div style='position: fixed; bottom: 0; left: 0; padding: 10px;'>
                <span>Version: {version}</span>
            </div>
        """
        st.markdown(footer_html, unsafe_allow_html=True)

    elif authentication_status is False:
        st.error("Username/password is incorrect")
    elif authentication_status is None:
        st.warning("Please enter your username and password")

if __name__ == "__main__":
    main()
