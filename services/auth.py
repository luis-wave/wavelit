import os

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


def authenticate_user():
    # Load configuration from the YAML file
    with open("utils/config.yaml") as file:
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

    return name, authentication_status, username, authenticator
