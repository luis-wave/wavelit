"""
    Load MeRT 2 data into session for Streamlit visualization.
"""

import streamlit as st

from services.mert2_data_management.mert_api import MeRTApi

api = MeRTApi()