"""
An EEG history component with variable report types.
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
            # Update session state instead of full rerun
            st.session_state.data_updated = True
        return

    # Check if EEG reports are loaded
    if "eeg_reports" not in st.session_state:
        st.info("Loading EEG reports...")
        if st.button("Load Reports"):
            asyncio.run(data_manager.load_eeg_reports())
            st.rerun()
        return

    eeg_data = st.session_state.all_eeg_info


    sorted_eeg_ids = []

    for eeg_id, details in eeg_data.items():

        response = asyncio.run(data_manager.api.get_eeg_report(eeg_id=eeg_id))

        report_lists = []

        if "neuroRefReports" in response and response["neuroRefReports"]:
            report_id = next(iter(response["neuroRefReports"]), None)
            report_type = "Neuroref"
            report_lists.append((report_id, report_type))

        if "neurorefcz" in response and response["neurorefcz"]:
            report_id = next(iter(response["neurorefcz"]), None)
            report_type = "Neuroref Cz"
            report_lists.append((report_id, report_type))

        if "documents" in response and response["documents"]:
            report_id = next(iter(response["documents"]), None)
            report_type = "Persyst"
            report_lists.append((report_id, report_type))


        if eeg_id.startswith("EEG-"):
            datetime_str = details.get('eegInfo', {}).get('dateTime', '')
            try:
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                sorted_eeg_ids.append((eeg_id, dt, details, report_lists))
            except (ValueError, AttributeError):
                # Fall back to recording date
                recording_date = details.get('baseProtocol', {}).get('recordingDate', '')
                try:
                    dt = datetime.fromisoformat(recording_date)
                    sorted_eeg_ids.append((eeg_id, dt, details, report_lists))
                except (ValueError, AttributeError):
                    # Use a default date for sorting if both are invalid
                    sorted_eeg_ids.append((eeg_id, datetime.min, details, report_lists))




    # Sort by date (most recent first)
    sorted_eeg_ids.sort(key=lambda x: x[1], reverse=True)

    # Display each EEG record in an expander
    for eeg_id, dt, details, report_lists in sorted_eeg_ids:
        file_name = details.get('eegInfo', {}).get('fileName', 'EEG File')
        review_state = details.get('eegInfo', {}).get('analysisMeta', {}).get('reviewState', '')

        # Format date
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

                            # Restore original EEG ID, don't want disrupt the current session in Wavelit
                            data_manager.eeg_id = temp_eeg_id

                        except Exception as e:
                            st.error(f"Error downloading EEG file: {str(e)}")

            # Column 2: Download Neurosynchrony Report
            with col2:
                if report_lists:

                    for idx,  (report_id, report_type) in enumerate(report_lists):
                        if st.button(f"Download {report_type} report", key=f"neuro_{eeg_id}_{idx}"):
                            with st.spinner("Downloading Neurosynchrony report..."):
                                try:
                                    # Save original EEG ID
                                    temp_eeg_id = data_manager.eeg_id
                                    data_manager.api.eeg_id = eeg_id

                                    if report_type == "Neuroref":
                                        report_content = asyncio.run(data_manager.api.download_neuroref_report(report_id=report_id))
                                        label = "Get Neuroref"
                                    elif report_type == "Neuroref Cz":
                                        report_content = asyncio.run(data_manager.api.download_neuroref_cz_report(report_id=report_id))
                                        label = "Get Neuroref Cz"
                                    elif report_type == "Persyst":
                                        report_content = asyncio.run(data_manager.api.download_document(document_id=report_id))
                                        label = "Get Persyst"
                                    else:
                                        label = None
                                        st.error(f"No report available")


                                    # Create download button
                                    st.download_button(
                                        label= label or "No report",
                                        data=report_content,
                                        file_name=f"{report_type}-{eeg_id}.pdf",
                                        mime="application/pdf",
                                        key=f"dl_neuro_{eeg_id}_{idx}"
                                    )

                                    # Restore original EEG ID
                                    data_manager.api.eeg_id = temp_eeg_id

                                except Exception as e:
                                    st.error(f"Error downloading Neurosynchrony report: {str(e)}")
                        st.divider()
                else:
                    st.write("No Neurosynchrony report available")

            # Column 3: Open in Lab
            with col3:
                lab_url = f"https://lab.wavesynchrony.com/?eegid={eeg_id}&pid={data_manager.patient_id}&clinicid={data_manager.clinic_id}"
                st.markdown(f"[Navigate to review case]({lab_url})")