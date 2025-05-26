import asyncio
from datetime import datetime, timedelta
import html
import streamlit as st

from utils.helpers import format_datetime, parse_recording_date
from utils.performance_cache import get_eeg_info_cached
from streamlit_apps.mert_components.review_utils import EEGReviewState




@st.fragment
def render_notes(data_manager, eeg_scientist_patient_notes):
    st.subheader("EEG Scientist Patient Notes")

    # Form for adding a new note
    with st.form("new_note_form"):
        st.write("Add New Note")
        eeg_info = get_eeg_info_cached(data_manager.patient_id, data_manager.eeg_id, data_manager.clinic_id)
        eeg_info_data = eeg_info["eegInfo"]
        dateTime = eeg_info_data["dateTime"]
        recording_dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M:%S.%fZ")

        # Convert to PST by subtracting 8 hours
        recording_dateTime_pst = recording_dateTime - timedelta(hours=8)

        st.date_input("Recording Date", value=recording_dateTime_pst, disabled=True)
        subject = st.text_input("Subject")
        content = st.text_area("Content")
        submitted = st.form_submit_button("Submit Note")

        eeg_info = get_eeg_info_cached(data_manager.patient_id, data_manager.eeg_id, data_manager.clinic_id)
        analysis_meta = eeg_info["eegInfo"]["analysisMeta"]
        current_state = (
            EEGReviewState[analysis_meta["reviewState"]]
            if analysis_meta["reviewState"]
            else EEGReviewState.PENDING
        )

        if current_state.name not in  ("CLINICAL_REVIEW", "REJECTED", "COMPLETED"):
            edit_note = st.form_submit_button("Edit Note")
        else:
            edit_note = None

        eeg_recording_date = recording_dateTime_pst.strftime(
                    "%a, %B %d %Y, %I:%M:%S %p"
                )

        if submitted:
            new_note = {
                "recordingDate": eeg_recording_date ,
                "subject": subject,
                "content": content,
                "dateEdited": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            }
            try:
                asyncio.run(data_manager.save_eeg_scientist_patient_note(new_note))
                st.success("Note added successfully!")
                # Update session state instead of full rerun
                st.session_state.data_updated = True
            except Exception as e:
                st.error(f"Failed to add note: {str(e)}")

        if edit_note:
            new_note = {
                "recordingDate": eeg_recording_date,
                "subject": subject,
                "content": content,
                "dateEdited": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            }
            try:
                asyncio.run(data_manager.save_eeg_scientist_patient_note(new_note, note_creation_date=eeg_recording_date))
                st.success("Note edited successfully!")
                # Update session state instead of full rerun
                st.session_state.data_updated = True
            except Exception as e:
                st.error(f"Failed to add note: {str(e)}")



    st.divider()

    if not eeg_scientist_patient_notes:
        st.write("No notes available.")
        return

    # Consolidate notes by recording date
    consolidated_notes = {}
    for date_key, note in eeg_scientist_patient_notes.items():
        # Store original format for API calls and sorting
        note["dateEditedIso"] = note["dateEdited"]
        
        # Keep the dateEdited field as-is for display
        # If it's already in user-friendly format (like "May 26, 2025 at 07:54 AM PDT"), display it
        # If it's in ISO format, it will be displayed as-is (no reformatting to avoid errors)
            
        recording_date = note["recordingDate"]
        if recording_date not in consolidated_notes:
            consolidated_notes[recording_date] = []
        consolidated_notes[recording_date].append(note)

    # Sort notes within each recording date by time of edit (newest first)
    def parse_date_safely(date_str):
        """Parse date string with multiple format attempts"""
        if not date_str:
            return datetime(1900, 1, 1)
        
        # Debug logging
        if st.session_state.get("debug_mode", False):
            st.write(f"DEBUG: Attempting to parse date: '{date_str}'")
            
        formats_to_try = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds
            "%Y-%m-%dT%H:%M:%SZ",     # ISO format without microseconds
            "%Y-%m-%dT%H:%M:%S",      # ISO format without Z
            "%b %d, %Y at %I:%M %p PST",  # Format like "Jan 04, 2024 at 04:10 PM PST"
            "%b %d, %Y at %I:%M %p PDT",  # Format like "Jan 04, 2024 at 04:10 PM PDT"
            "%b %d, %Y at %I:%M %p",   # Format without timezone
            "%Y-%m-%d %H:%M:%S",       # Standard datetime format
            "%Y-%m-%d",                # Just date
        ]
        
        for fmt in formats_to_try:
            try:
                result = datetime.strptime(date_str, fmt)
                if st.session_state.get("debug_mode", False):
                    st.write(f"DEBUG: Successfully parsed with format '{fmt}': {result}")
                return result
            except ValueError:
                continue
        
        # If all formats fail, try to extract just the date part and use a default time
        try:
            # Try to parse just the date part
            date_part = date_str.split(" at ")[0] if " at " in date_str else date_str
            result = datetime.strptime(date_part, "%b %d, %Y")
            if st.session_state.get("debug_mode", False):
                st.write(f"DEBUG: Parsed date part '{date_part}': {result}")
            return result
        except ValueError:
            pass
            
        # Try to handle other common formats
        try:
            # Handle formats like "Jan 4, 2024" (without leading zero) by normalizing
            date_part = date_str.split(" at ")[0] if " at " in date_str else date_str
            # Try to normalize the day part by adding leading zero if needed
            import re
            normalized_date = re.sub(r'\b(\d)\b', r'0\1', date_part)
            result = datetime.strptime(normalized_date, "%b %d, %Y")
            if st.session_state.get("debug_mode", False):
                st.write(f"DEBUG: Parsed normalized date '{normalized_date}': {result}")
            return result
        except (ValueError, ImportError):
            pass
            
        # Last resort: return a very old date so it sorts to the bottom
        st.warning(f"Could not parse date: '{date_str}'. Using fallback date for sorting.")
        return datetime(1900, 1, 1)
    
    for recording_date in consolidated_notes:
        try:
            consolidated_notes[recording_date] = sorted(
                consolidated_notes[recording_date],
                key=lambda n: parse_date_safely(n["dateEditedIso"]),
                reverse=True,  # Using True to put newest notes at the top
            )
        except Exception as e:
            st.error(f"Error sorting notes for {recording_date}: {str(e)}")
            # Show the problematic data for debugging
            st.write("Problematic note data:")
            for note in consolidated_notes[recording_date]:
                st.write(f"dateEditedIso: '{note.get('dateEditedIso', 'MISSING')}'")
            # Keep unsorted as fallback
            pass

    # Sort recording dates in descending order
    sorted_recording_dates = sorted(
        consolidated_notes.keys(),
        key=lambda d: parse_recording_date(d),
        reverse=True
    )

    # Render notes with preserved formatting
    for recording_date in sorted_recording_dates:
        notes = consolidated_notes[recording_date]

        st.markdown(f"### Notes from {recording_date}", help="Recording date of the EEG session")
        for note in notes:
            # Escape HTML special characters and preserve line breaks
            safe_content = html.escape(note['content'])
            formatted_content = safe_content.replace('\n', '<br>')

            st.markdown(
                f"""
                <div style="background-color: #f9f9f9;
                            padding: 10px;
                            margin-bottom: 8px;
                            border-radius: 5px;
                            white-space: pre-wrap;
                            font-family: inherit;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px;">
                        <strong>{html.escape(note['subject'])}</strong>
                        <em style="font-size: 0.9em;">Edited: {note["dateEdited"]}</em>
                    </div>
                    <div style="white-space: pre-wrap; margin-top: 4px;">{formatted_content}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.divider()