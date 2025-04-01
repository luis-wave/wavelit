import asyncio
from datetime import datetime, timedelta
import html
import streamlit as st

from utils.helpers import format_datetime, parse_recording_date
from streamlit_apps.mert_components.review_utils import EEGReviewState


@st.fragment
def render_notes(data_manager, eeg_scientist_patient_notes):
    st.subheader("EEG Scientist Patient Notes")

    # Form for adding a new note
    with st.form("new_note_form"):
        st.write("Add New Note")
        eeg_info = asyncio.run(data_manager.fetch_eeg_info_by_patient_id_and_eeg_id())
        eeg_info_data = eeg_info["eegInfo"]
        dateTime = eeg_info_data["dateTime"]
        recording_dateTime = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M:%S.%fZ")

        # Convert to PST by subtracting 8 hours
        recording_dateTime_pst = recording_dateTime - timedelta(hours=8)

        st.date_input("Recording Date", value=recording_dateTime_pst, disabled=True)
        subject = st.text_input("Subject")
        content = st.text_area("Content")
        submitted = st.form_submit_button("Submit Note")

        eeg_info = asyncio.run(data_manager.fetch_eeg_info_by_patient_id_and_eeg_id())
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
                st.rerun()  # Rerun the app to refresh the notes list
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
                st.rerun()  # Rerun the app to refresh the notes list
            except Exception as e:
                st.error(f"Failed to add note: {str(e)}")



    st.divider()

    if not eeg_scientist_patient_notes:
        st.write("No notes available.")
        return

    # Consolidate notes by recording date
    consolidated_notes = {}
    for date_key, note in eeg_scientist_patient_notes.items():
        # Store original ISO format for sorting before formatting for display
        note["dateEditedIso"] = note["dateEdited"]
        note["dateEdited"] = format_datetime(note["dateEdited"])
        recording_date = note["recordingDate"]
        if recording_date not in consolidated_notes:
            consolidated_notes[recording_date] = []
        consolidated_notes[recording_date].append(note)

    # Sort notes within each recording date by time of edit (newest first)
    for recording_date in consolidated_notes:
        consolidated_notes[recording_date] = sorted(
            consolidated_notes[recording_date],
            key=lambda n: datetime.strptime(n["dateEditedIso"], "%Y-%m-%dT%H:%M:%S.%fZ"),
            reverse=True,  # Using True to put newest notes at the top
        )

    # Sort recording dates in descending order
    sorted_recording_dates = sorted(
        consolidated_notes.keys(),
        key=lambda d: parse_recording_date(d),
        reverse=True
    )

    # Render notes with preserved formatting
    for recording_date in sorted_recording_dates:
        notes = consolidated_notes[recording_date]
        times = recording_date.split(' ')
        dow = times[0]
        month = times[1]
        day = times[2]
        year = times[3]
        toeeg = times[4] + ' ' + times[5]
        timeHold = dow + ' ' + month + ' ' + day[0:-2] + ' ' + year + ' ' + toeeg

        recording_dateTime = datetime.strptime(timeHold, "%a, %B %d %Y, %I:%M:%S %p")
        st.markdown(f"### Notes from {recording_date}", help="Recording date of the EEG session")
        for note in notes:
            st.date_input("Recording Date", value=recording_dateTime, disabled=True)
            st.date_input("Date Edited", value=note["dateEdited"], disabled=True)
            subject = note["subject"]
            content = note['content']
            edit_note = st.form_submit_button("Edit Note")
            if edit_note:
                new_note = {
                    "recordingDate": recording_date, 
                    "subject": subject,
                    "content": content,
                    "dateEdited": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                }
                try:
                    asyncio.run(data_manager.save_eeg_scientist_patient_note(new_note, note_creation_date=recording_date))
                    st.success("Note edited successfully!")
                    st.rerun()  # Rerun the app to refresh the notes list
                except Exception as e:
                    st.error(f"Failed to add note: {str(e)}")
        st.divider()
