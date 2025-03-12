"""
A clean EEG history component with fixed report association.
"""

import asyncio
from datetime import datetime
import streamlit as st


@st.fragment
def render_eeg_history(data_manager):
    st.subheader("EEG History")

    # Check if EEG data is loaded
    if "all_eeg_info" not in st.session_state:
        st.warning("EEG data not loaded. Please load the data first.")
        if st.button("Load EEG Data"):
            asyncio.run(data_manager.load_all_eeg_info())
            st.rerun()
        return

    # Check if EEG reports are loaded
    if "eeg_reports" not in st.session_state:
        st.info("Loading EEG reports...")
        if st.button("Load Reports"):
            asyncio.run(data_manager.load_eeg_reports())
            st.rerun()
        return

    eeg_data = st.session_state.all_eeg_info
    eeg_reports = st.session_state.get("eeg_reports", {})

    # Extract neuroref reports
    neuroref_reports = eeg_reports.get("neuroRefReports", {})

    # Sort EEGs by recording date (most recent first)
    sorted_eeg_ids = []
    for eeg_id, details in eeg_data.items():
        if eeg_id.startswith("EEG-"):
            datetime_str = details.get('eegInfo', {}).get('dateTime', '')
            try:
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                sorted_eeg_ids.append((eeg_id, dt, details))
            except (ValueError, AttributeError):
                # Fall back to recording date
                recording_date = details.get('baseProtocol', {}).get('recordingDate', '')
                try:
                    dt = datetime.fromisoformat(recording_date)
                    sorted_eeg_ids.append((eeg_id, dt, details))
                except (ValueError, AttributeError):
                    # Use a default date for sorting if both are invalid
                    sorted_eeg_ids.append((eeg_id, datetime.min, details))

    # Sort by date (most recent first)
    sorted_eeg_ids.sort(key=lambda x: x[1], reverse=True)

    # Display each EEG record in an expander
    for eeg_id, dt, details in sorted_eeg_ids:
        file_name = details.get('eegInfo', {}).get('fileName', 'EEG File')
        review_state = details.get('eegInfo', {}).get('analysisMeta', {}).get('reviewState', '')

        # Format date nicely
        try:
            formatted_date = dt.strftime("%Y-%m-%d %H:%M")
        except:
            formatted_date = "Unknown Date"

        # Format review state text
        if review_state == "CLINIC_REVIEW":
            state_text = "Clinic Review"
        elif review_state == "REVIEW_PENDING":
            state_text = "Review Pending"
        elif review_state == "REJECTED":
            state_text = "Rejected"
        elif review_state == "REVIEW_COMPLETE":
            state_text = "Complete"
        else:
            state_text = "Not Reviewed"

        # Create expander label with date and review state
        expander_label = f"{formatted_date} - {state_text}"

        with st.expander(expander_label, expanded=False):
            # Create a clean layout with three columns
            col1, col2, col3 = st.columns(3)

            # Column 1: Download EEG File
            with col1:
                if st.button("Download EEG File", key=f"eeg_{eeg_id}"):
                    with st.spinner("Downloading EEG file..."):
                        try:
                            # Save original EEG ID
                            temp_eeg_id = data_manager.eeg_id
                            data_manager.eeg_id = eeg_id

                            # Download EEG file
                            eeg_content = asyncio.run(data_manager.download_eeg_file())

                            # Create download button
                            st.download_button(
                                label="Get EEG File",
                                data=eeg_content,
                                file_name=file_name,
                                mime="application/octet-stream",
                                key=f"dl_eeg_{eeg_id}"
                            )

                            # Restore original EEG ID
                            data_manager.eeg_id = temp_eeg_id

                        except Exception as e:
                            st.error(f"Error downloading EEG file: {str(e)}")

            # Column 2: Download Neurosynchrony Report
            with col2:
                if neuroref_reports:
                    # Get a list of report IDs
                    report_ids = list(neuroref_reports.keys())
                    if report_ids:
                        report_id = report_ids[0]  # Get first report ID

                        if st.button("Download report", key=f"neuro_{eeg_id}"):
                            with st.spinner("Downloading Neurosynchrony report..."):
                                try:
                                    # Save original EEG ID
                                    temp_eeg_id = data_manager.eeg_id
                                    data_manager.eeg_id = eeg_id

                                    # Download report
                                    report_content = asyncio.run(data_manager.api.download_neuroref_report(report_id=report_id))

                                    # Create download button
                                    st.download_button(
                                        label="Get report",
                                        data=report_content,
                                        file_name=f"Neurosynchrony-{eeg_id}.pdf",
                                        mime="application/pdf",
                                        key=f"dl_neuro_{eeg_id}"
                                    )

                                    # Restore original EEG ID
                                    data_manager.eeg_id = temp_eeg_id

                                except Exception as e:
                                    st.error(f"Error downloading Neurosynchrony report: {str(e)}")
                    else:
                        st.write("No Neurosynchrony report available")
                else:
                    st.write("No Neurosynchrony report available")

            # Column 3: Open in Lab
            with col3:
                lab_url = f"https://lab.wavesynchrony.com/?eegid={eeg_id}&pid={data_manager.patient_id}&clinicid={data_manager.clinic_id}"
                st.markdown(f"[Open in Lab]({lab_url})")