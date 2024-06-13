import os
import streamlit as st
import toml
from services.eeg_data_manager import EEGDataManager
from services.auth import authenticate_user
import traceback
import asyncio

st.session_state.heart_rate = None
st.session_state.eqi = None

# Function to read version from pyproject.toml
def get_version_from_pyproject():
    try:
        pyproject_data = toml.load("pyproject.toml")
        return pyproject_data["tool"]["poetry"]["version"]
    except Exception as e:
        st.error(f"Error reading version from pyproject.toml: {e}")
        return "Unknown"

async def main():
    name, authentication_status, username, authenticator = authenticate_user()

    if authentication_status:
        authenticator.logout("Logout", "main")
        st.write(f'Welcome *{name}*')

        base_url = os.getenv("BASE_URL")
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        api_key = os.getenv("API_KEY")

        eeg_manager = EEGDataManager(base_url, username, password, api_key)
        await eeg_manager.initialize()

        st.title("EEG Analysis Dashboard")

        # Upload EEG file
        uploaded_file = st.file_uploader("Upload an EEG file", type=["dat", "edf"])

        if uploaded_file is not None:
            try:
                await eeg_manager.handle_uploaded_file(uploaded_file)
                st.switch_page("pages/🏄 epochs.py")
            except Exception as e:
                tb_exception = traceback.TracebackException.from_exception(e)
                st.error(f"File upload or processing failed: {''.join(tb_exception.format())}")

        # Download EEG file by EEG ID
        st.write("Or")
        eeg_id = st.text_input("Enter EEG ID")

        if st.button("Download EEG Data"):
            with st.spinner("Downloading EEG data..."):
                try:
                    await eeg_manager.handle_downloaded_file(eeg_id)
                    await eeg_manager.fetch_additional_data(eeg_id)
                    st.switch_page("pages/🏄 epochs.py")
                except Exception as e:
                    tb_exception = traceback.TracebackException.from_exception(e)
                    st.error(f"Data retrieval or processing failed: {''.join(tb_exception.format())}")

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
    asyncio.run(main())
