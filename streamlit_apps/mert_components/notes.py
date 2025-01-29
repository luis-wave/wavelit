"""
Renders the notes from MeRT 2. Once notes are submitted, they can't be edited or deleted.
Do not alter this functionality.
"""

import asyncio
from datetime import datetime

import streamlit as st

from utils.helpers import format_datetime, parse_recording_date


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
        st.date_input("Recording Date", value=recording_dateTime, disabled=True)
        subject = st.text_input("Subject")
        content = st.text_area("Content")
        submitted = st.form_submit_button("Submit Note")

        if submitted:
            new_note = {
                "recordingDate": recording_dateTime.strftime(
                    "%a, %B %d %Y, %I:%M:%S %p"
                ),
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

    st.divider()

    if not eeg_scientist_patient_notes:
        st.write("No notes available.")
        return

    # Consolidate notes by recording date
    consolidated_notes = {}
    for date_key, note in eeg_scientist_patient_notes.items():
        # Convert to PST
        note["dateEdited"] = format_datetime(note["dateEdited"])
        recording_date = note["recordingDate"]
        if recording_date not in consolidated_notes:
            consolidated_notes[recording_date] = []
        consolidated_notes[recording_date].append(note)

    # Sort notes within each recording date by time of edit (newest last)
    for recording_date in consolidated_notes:
        consolidated_notes[recording_date] = sorted(
            consolidated_notes[recording_date],
            key=lambda n: n["dateEdited"],
            reverse=True,
        )




    # Sort the recording dates (keys) in descending order by date
    sorted_recording_dates = sorted(
        consolidated_notes.keys(),
        key=lambda d: parse_recording_date(d),
        reverse=True  # True -> most recent first
    )

    # Now iterate over the sorted dates
    for recording_date in sorted_recording_dates:
        notes = consolidated_notes[recording_date]

        st.markdown(f"### Notes from {recording_date}")
        for idx, note in enumerate(notes, start=1):
            st.markdown(
                f"""
                <div style="background-color: #f9f9f9;
                            padding: 10px;
                            margin-bottom: 10px;
                            border-radius: 5px;">
                    <strong>{note['subject']}</strong><br />
                    <em>Edited on: {note['dateEdited']}</em><br /><br />
                    {note['content']}
                </div>
                """,
                unsafe_allow_html=True
            )
        st.divider()

