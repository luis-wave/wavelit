"""
Renders the notes from MeRT 2. Once notes are submitted, they can't be edited or deleted.
Do not alter this functionality.
"""

import asyncio

import streamlit as st


@st.fragment
def render_notes(data_manager, eeg_scientist_patient_notes):
    st.subheader("EEG Scientist Patient Notes")

    # Form for adding a new note
    with st.form("new_note_form"):
        st.write("Add New Note")
        eeg_info = asyncio.run(data_manager.fetch_eeg_info_by_patient_id_and_eeg_id())
        dateTime = eeg_info_data['dateTime']
        recording_dateTime = datetime.strptime(dateTime, '%Y-%m-%dT%H:%M:%S.%fZ')
        recording_date = st.date_input("Recording Date", value = recording_dateTime, disabled=True)
        subject = st.text_input("Subject")
        content = st.text_area("Content")
        submitted = st.form_submit_button("Submit Note")

        if submitted:
            new_note = {
                "recordingDate": recording_dateTime.strftime('%a, %B %d %Y, %I:%M:%S %p'),
                "subject": subject,
                "content": content,
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

    # Sort notes by date (newest first)
    sorted_notes = sorted(
        eeg_scientist_patient_notes.items(), key=lambda x: x[0], reverse=True
    )

    for date, note in sorted_notes:
        st.markdown(f"### {note['subject']} - {note['recordingDate']}")
        st.write(f"**Date Edited:** {note['dateEdited']}")
        st.write(f"**Recording Date:** {note['recordingDate']}")
        st.write(f"**Subject:** {note['subject']}")
        st.write("**Content:**")

        # Display content in a text area
        st.text_area(
            "", value=note["content"], height=150, key=f"note_{date}", disabled=True
        )

        st.divider()
