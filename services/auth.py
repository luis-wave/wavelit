import os

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


def authenticate_user():
    # Load configuration from the YAML file
    with open("config.yaml") as file:
        config = yaml.load(file, Loader=SafeLoader)

    # Initialize the authenticator
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    # Get the username, authentication status, and name
    name, authentication_status, username = authenticator.login()

    # Ensure username is not None
    if username is None or username not in config["credentials"]["usernames"]:
        st.error("Invalid username or authentication failed.")
        return None, False, None, authenticator

    user_config = config["credentials"]["usernames"][username]

    st.session_state["name"] = name
    st.session_state["id"] = user_config["id"]
    st.session_state["m2_username"] = user_config["m2_username"]

    return name, authentication_status, username, authenticator
