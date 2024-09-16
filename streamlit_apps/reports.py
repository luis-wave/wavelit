"""
Landing page for EEG report review and approval workflow.
"""

import streamlit as st

from services.mert2_data_management.mert_api import MeRTApi



api = MeRTApi()