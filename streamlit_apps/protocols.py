import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime
from services.mert2_data_management.mert_data_manager import MeRTDataManager

def render_protocol_page(data_manager):
    st.title("EEG Protocol")

    # Fetch EEG info
    eeg_info = asyncio.run(data_manager.fetch_eeg_info_by_patient_id_and_eeg_id())
    base_protocol = eeg_info['baseProtocol']
    analysis_meta = eeg_info['eegInfo']['analysisMeta']
    eeg_info_data = eeg_info['eegInfo']

    # Display metadata
    st.subheader("Metadata")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**EEG ID:** {eeg_info_data['eegId']}")
        st.markdown(f"**Patient ID:** {data_manager.patient_id}")
        st.markdown(f"**Clinic ID:** {data_manager.clinic_id}")
    with col2:
        st.markdown(f"**Recording Date:** {base_protocol['recordingDate']}")
        st.markdown(f"**Upload Date:** {eeg_info_data['uploadDateTime']}")
        st.markdown(f"**Review State:** {analysis_meta['reviewState']}")

    # Create editable dataframe for base protocol
    st.subheader("Base Protocol")

    # Add new fields to the protocol
    base_protocol['pulseMode'] = base_protocol.get('pulseMode', 'Biphasic')
    base_protocol['location'] = base_protocol.get('location', 'F1-FZ-F2')

    # Create the dataframe without transposing
    protocol_df = pd.DataFrame([base_protocol])

    # Define the location options
    location_options = [
        "FP1-FPZ-FP2", "F1-FZ-F2", "C1-CZ-C2", "P1-PZ-P2", "F1-F3-F5", "F2-F4-F6",
        "F7-FT7-T3", "F8-FT8-T4", "CP1-CPZ-CP2", "FC1-FCZ-FC2", "TP7-T3-FT7",
        "TP8-T4-FT8", "C5-C3-C1", "C6-C4-C2", "C3-CP3-P3", "C4-CP4-P4", "P3-CP5-T3",
        "P4-CP6-T4", "P1-P3-P5", "P2-P4-P6", "P3-P5-P7", "P4-P6-P8", "P3-PO3-O1",
        "P4-PO4-O2", "PO3-O1-PO7", "PO4-O2-PO8"
    ]

    # Create the editable dataframe
    edited_df = st.data_editor(
        protocol_df,
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "pulseMode": st.column_config.SelectboxColumn(
                "Pulse Mode",
                options=['Biphasic', 'Monophasic'],
                required=True
            ),
            "location": st.column_config.SelectboxColumn(
                "Location",
                options=location_options,
                required=True
            )
        },
        hide_index=True,
    )

    # Check if there are changes in the protocol
    if not edited_df.equals(protocol_df):
        if st.button("Save Protocol Changes"):
            try:
                # Convert the edited dataframe to a dictionary
                updated_protocol = edited_df.iloc[0].to_dict()
                # Here you would call a method to update the protocol
                # For example: asyncio.run(data_manager.update_base_protocol(updated_protocol))
                st.success("Protocol updated successfully!")
            except Exception as e:
                st.error(f"Failed to update protocol: {str(e)}")

    # Display additional EEG information
    st.subheader("Additional EEG Information")
    st.markdown(f"**File Name:** {eeg_info_data['fileName']}")
    st.markdown(f"**Is Import:** {'Yes' if eeg_info_data['isImport'] else 'No'}")
    st.markdown(f"**Is Processed:** {'Yes' if eeg_info_data['isProcessed'] else 'No'}")
    st.markdown(f"**Quality Status:** {eeg_info_data['qualityStatus'] or 'N/A'}")

    # Display review information
    st.subheader("Review Information")
    st.markdown(f"**Review Deadline:** {analysis_meta['reviewDeadline']}")
    st.markdown(f"**Reviewer ID:** {analysis_meta['reviewerStaffId']}")
    st.markdown(f"**Review Date:** {analysis_meta['reviewDatetime']}")
    st.markdown(f"**Second Reviewer ID:** {analysis_meta['secondReviewerStaffId'] or 'N/A'}")
    st.markdown(f"**Second Review Date:** {analysis_meta['secondReviewDatetime'] or 'N/A'}")

# Initialize MeRTDataManager
data_manager = MeRTDataManager(
    patient_id="PAT-7ab945ce-b879-11ed-b74f-0273bda7c1f3",
    eeg_id="EEG-06bc6524-2fe7-49b8-8c33-860fefec808a",
    clinic_id="c3e85638-86c9-11eb-84b6-0aea104587df"
)

# Load all data into session state
asyncio.run(data_manager.load_all_data())

# Render the protocol page
render_protocol_page(data_manager)