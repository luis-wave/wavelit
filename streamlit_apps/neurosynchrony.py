
"""
Set up the primary UI for eeg report and protocol review.
"""

import asyncio
import logging
import os
import pandas as pd

import streamlit as st
import streamlit.components.v1 as components
from streamlit_pdf_viewer import pdf_viewer

from access_control import access_eeg_data
from services.mert2_data_management.mert_data_manager import MeRTDataManager
from streamlit_apps.mert_components import (render_abnormalities,
                                            render_artifact_distortions,
                                            render_documents,
                                            render_eeg_review, render_notes,
                                            render_protocol_page,
                                            get_report_addendum_eeg_id,
                                            render_eeg_history)
from streamlit_dashboards import eeg_visualization_dashboard
from streamlit_dashboards import ecg_visualization_dashboard
from utils.helpers import calculate_age
import streamlit_shadcn_ui as ui
from streamlit_apps.mert_components.review_utils import EEGReviewState


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


data_manager = None
base_url=None

if (
    ("eegid" in st.session_state)
    and ("pid" in st.session_state)
    and ("clinicid" in st.session_state)
):


    addendum_eeg_id = st.session_state.get("addendum_eeg_id", None)


    if addendum_eeg_id:
        st.session_state["addendum"] = True
         # Initialize MeRTDataManager
        data_manager = MeRTDataManager(
            patient_id=st.session_state["pid"],
            eeg_id=addendum_eeg_id,
            clinic_id=st.session_state["clinicid"],
        )
        # Load all data into session state
        asyncio.run(data_manager.load_all_data())

        # If in addendum mode and we have the original EEG ID stored
        asyncio.run(access_eeg_data(st.session_state["eegid"]))

        st.header("Addendum")

        base_url = "https://lab.wavesynchrony.com"
        base_url = base_url + f"/?pid={st.session_state['pid']}&eegid={addendum_eeg_id}&clinicid={st.session_state['clinicid']}"

    else:
        # Initialize MeRTDataManager
        data_manager = MeRTDataManager(
            patient_id=st.session_state["pid"],
            eeg_id=st.session_state["eegid"],
            clinic_id=st.session_state["clinicid"],
        )

        # Load all data into session state
        asyncio.run(data_manager.load_all_data())
        # Default behavior - use current EEG ID
        asyncio.run(access_eeg_data(st.session_state["eegid"]))


        base_url = "https://lab.wavesynchrony.com"
        base_url = base_url + f"/?pid={st.session_state['pid']}&eegid={st.session_state['eegid']}&clinicid={st.session_state['clinicid']}"


# Callback function to handle EEG selection
def on_eeg_selected():
    """Process the EEG selection and fetch data asynchronously"""
    # Get the selected EEG ID from the dropdown options
    selected_display = st.session_state.eeg_dropdown

    # Get all the dropdown options
    eeg_df = st.session_state.eeg_history
    options = []
    for idx in eeg_df["EEGId"].keys():
        eeg_id = eeg_df["EEGId"][idx]
        recording_date = eeg_df["RecordingDate"][idx].strftime("%b %d, %Y")
        display_text = f"{eeg_id} ({recording_date})"
        options.append((display_text, eeg_id))

    # Find the matching EEG ID from the selected display text
    selected_eeg_id = next((opt[1] for opt in options if opt[0] == selected_display), None)

    # Run the data access function
    if selected_eeg_id:
        st.session_state.eegid = selected_eeg_id


def eeg_dropdown():
    """Create the EEG dropdown menu"""
    if "eeg_history" not in st.session_state:
        return None

    # Get the data from session state
    eeg_df = st.session_state.eeg_history

    # Create options for dropdown
    options = []
    for idx in eeg_df["EEGId"].keys():
        eeg_id = eeg_df["EEGId"][idx]
        # Format the recording date in mm-dd-yyyy format
        recording_date = (
            "Unknown Date" if pd.isna(eeg_df["RecordingDate"][idx])
            else eeg_df["RecordingDate"][idx].strftime("%b %d, %Y")
        )
        display_text = f"{eeg_id} ({recording_date})"
        options.append((display_text, eeg_id))

    # Initialize selected_eeg in session state if it doesn't exist
    if 'selected_eeg' not in st.session_state and options:
        st.session_state.selected_eeg = options[0][1]

    # Create dropdown with formatted options
    selected_option = st.selectbox(
        "Select EEG:",
        options=[option[0] for option in options],
        index=0 if options else None,
        key="eeg_dropdown",
        on_change=on_eeg_selected
    )

    return selected_option






def delete_report(data_manager, report_id, ref="default"):
    if ref == "default":
        asyncio.run(data_manager.delete_neuroref_report(report_id))
        st.success(f"Neuroref {report_id} successfully deleted!")
        st.rerun()
    elif ref == "cz":
        asyncio.run(data_manager.delete_neuroref_cz_report(report_id))
        st.success(f"Neuroref Cz {report_id} successfully deleted!")
        st.rerun()

eeg_dropdown()

if "tab" in st.session_state:
    if st.session_state['tab'] == "Protocols":
        tabs = ["Protocols", "Reports", "EEG", "ECG"]
        tab1, tab2, tab3, tab4 = st.tabs(tabs)

else:
  tabs = ["Reports", "Protocols", "EEG", "ECG"]
  tab2, tab1, tab3, tab4 = st.tabs(tabs)


with tab1:
    render_protocol_page(data_manager)


with tab2:
    # Start rendering the UI
    st.title("NeuroSynchrony Review")

    if base_url:
        # Display the copy button
        st.write("Copy URL:")
        full_url = f'''{base_url}'''
        st.code(full_url, language="python", wrap_lines=True)


    col1, col2 = st.columns(2)

    with col1:
        st.write("PatientId:")
        full_pid = f'''{st.session_state['pid']}'''
        st.code(full_pid, language="python", wrap_lines=True)

        patient_data = st.session_state.patient_data
        clinic_info = st.session_state.clinic_info

        first_name = patient_data["profileInfo"]["name"]["first"]
        last_name = patient_data["profileInfo"]["name"]["last"]
        middle_name = patient_data["profileInfo"]["name"]["middle"]
        username = patient_data["profileInfo"]["username"]
        dob = patient_data["profileInfo"]["dateOfBirth"]
        age = calculate_age(dob)
        sex = patient_data["profileInfo"]["sex"].capitalize()
        patient_id = patient_data["profileInfo"]["patientId"]
        primary_complaint = patient_data.get("clinicalInfo", {}).get("primaryComplaint", "Not Provided")
        is_having_seizures = (
            "Yes" if patient_data["clinicalInfo"]["isHavingSeizures"] else "No"
        )

        if "CORTICAL" in st.session_state.treatment_count:
            treatment_count = st.session_state.treatment_count["CORTICAL"]
        else:
            treatment_count = 0

with col1:
    patient_data = st.session_state.patient_data
    clinic_info = st.session_state.clinic_info

    first_name = patient_data["profileInfo"]["name"]["first"]
    last_name = patient_data["profileInfo"]["name"]["last"]
    middle_name = patient_data["profileInfo"]["name"]["middle"]
    username = patient_data["profileInfo"]["username"]
    dob = patient_data["profileInfo"]["dateOfBirth"]
    age = calculate_age(dob)
    sex = patient_data["profileInfo"]["sex"].capitalize()
    patient_id = patient_data["profileInfo"]["patientId"]
    primary_complaint = patient_data.get("clinicalInfo", {}).get("primaryComplaint", "Not Provided")
    is_having_seizures = (
        "Yes" if patient_data["clinicalInfo"]["isHavingSeizures"] else "No"
    )

    if "CORTICAL" in st.session_state.treatment_count:
        treatment_count = st.session_state.treatment_count["CORTICAL"]
    else:
        treatment_count = 0


    with ui.card(key="patient_card"):
        # Patient Name
        ui.element("h2",
                children=[f"{first_name} {middle_name + ' ' if middle_name else ''}{last_name}"],
                className="text-2xl font-bold mb-4",
                key="name")

        # Patient ID and Username
        ui.element("span", children=["Patient ID"], className="text-gray-500 text-sm font-medium", key="id_label")
        ui.element("div", children=[patient_id], className="mb-2", key="id_value")

        ui.element("span", children=["Username"], className="text-gray-500 text-sm font-medium", key="username_label")
        ui.element("div", children=[username], className="mb-4", key="username_value")

        ui.element("hr", className="my-4", key="divider1")

        # Demographics
        ui.element("span", children=["Sex"], className="text-gray-500 text-sm font-medium", key="sex_label")
        ui.element("div", children=[sex], className="mb-2", key="sex_value")

        ui.element("span", children=["Date of Birth"], className="text-gray-500 text-sm font-medium", key="dob_label")
        ui.element("div", children=[f"{dob}"], key="dob_value1")
        ui.element("span", children=[f"{age} years old"], className="font-bold", key="age_value")
        ui.element("div", children=[")"], className="mb-2", key="dob_value2")

        ui.element("span", children=["Treatment Sessions"], className="text-gray-500 text-sm font-medium", key="sessions_label")
        ui.element("div", children=[str(treatment_count)], className="mb-4", key="sessions_value")

        # Seizure Status
        if is_having_seizures == "Yes":
            ui.element("div",
                    children=["⚠️ Active Seizure History"],
                    className="bg-red-100 text-red-700 p-2 rounded mb-4",
                    key="seizure_status"
                    )

        # Primary Complaint
        ui.element("h3", children=["Primary Complaint"], className="text-lg font-medium mb-2", key="complaint_header")
        ui.element("div",
                children=[primary_complaint],
                className="bg-gray-50 p-3 rounded mb-4",
                key="complaint_value"
                )

        ui.element("hr", className="my-4", key="divider2")

        # Clinic Information
        ui.element("h3", children=[clinic_info["name"]], className="text-lg font-medium mb-2", key="clinic_name")

        ui.element("span", children=["Clinic ID"], className="text-gray-500 text-sm font-medium", key="clinic_id_label")
        ui.element("div", children=[clinic_info['clinicId']], className="mb-2", key="clinic_id_value")

        ui.element("span", children=["Phone"], className="text-gray-500 text-sm font-medium", key="phone_label")
        ui.element("div", children=[clinic_info['phone']], className="mb-2", key="phone_value")

        ui.element("span", children=["Location"], className="text-gray-500 text-sm font-medium", key="location_label")
        ui.element("div",
                children=[f"{clinic_info['address']['city']}, {clinic_info['address']['state']}, {clinic_info['address']['country']}"],
                className="mb-2",
                key="location_value"
                )


    if "eegScientistPatientNotes" in patient_data:
        eeg_scientist_patient_notes = patient_data["eegScientistPatientNotes"]
    else:
        eeg_scientist_patient_notes = None

    render_notes(data_manager, eeg_scientist_patient_notes)

    with col2:
        render_eeg_review(data_manager)


        st.subheader("Reports")


        eeg_info = asyncio.run(data_manager.fetch_eeg_info_by_patient_id_and_eeg_id())
        analysis_meta = eeg_info["eegInfo"]["analysisMeta"]
        eeg_filename = eeg_info["eegInfo"]['fileName']
        current_state = (
            EEGReviewState[analysis_meta["reviewState"]]
            if analysis_meta["reviewState"]
            else EEGReviewState.PENDING
        )

        if current_state.name == 'COMPLETED':
            if st.button(label="Add addendum", key="appended"):
                eeg_id = st.session_state['eegid']
                addendum_eeg_id = get_report_addendum_eeg_id(data_manager)
                st.session_state["addendum"] = True
                patient_id = st.session_state["pid"]
                clinic_id = st.session_state["clinicid"]
                url=f"https://lab.wavesynchrony.com/?eegid={eeg_id}&pid={patient_id}&clinicid={clinic_id}&addendum_eeg_id={addendum_eeg_id}"
                st.markdown(f'<meta http-equiv="refresh" content="0; url={url}">', unsafe_allow_html=True)
            else:
                st.session_state["addendum"] = False

        addendum = st.session_state.get("addendum", None)


        eeg_history_df = st.session_state.eeg_history

        if "downloaded_neuroref_report" in st.session_state:
            for idx, report_data in enumerate(
                st.session_state.downloaded_neuroref_report
            ):
                report, report_id = report_data
                pdf_viewer(report, height=1000, width=990, key=f"linked_ears {idx}")
                st.download_button(
                    label="Download Neuroref",
                    data=report,
                    file_name=f"Neurosynchrony-{report_id}.pdf",
                    key=f"download-{report_id}",
                )
                if st.button(label="Delete", key=f"Neurosynchrony-{report_id}"):
                    delete_report(data_manager, report_id)
                    st.success(f"Neuroref {report_id} successfully deleted!")

        if "downloaded_neuroref_cz_report" in st.session_state:
            for idx, report_data in enumerate(
                st.session_state.downloaded_neuroref_cz_report
            ):
                report, report_id = report_data
                pdf_viewer(report, height=1000,width=990, key=f"centroid {idx}")
                st.download_button(
                    label="Download Neuroref Cz",
                    data=report,
                    file_name=f"Neurosynchrony-Cz-{report_id}.pdf",
                    key=f"download-cz-{report_id}",
                )
                if st.button(label="Delete", key=f"Neurosynchrony-cz-{report_id}"):
                    delete_report(data_manager, report_id, ref="cz")
                    st.success(f"Neuroref Cz {report_id} successfully deleted!")



        # Swap out original filename with eeg id, life is better that way.
        base, ext = os.path.splitext(os.path.basename(eeg_filename))
        new_filename = eeg_filename.replace(base, st.session_state.eegid)

        if st.download_button(label="Download EEG", data= asyncio.run(data_manager.download_eeg_file()), mime="application/octet-stream", file_name=new_filename):
            pass


        st.header("EEG History")
        with st.form("data_editor_form", border=False):
            edited_eeg_history_df = st.data_editor(eeg_history_df, hide_index=True)
            regenerate_neuroref = st.form_submit_button("Generate Neuroref Report")
            regenerate_neuroref_cz = st.form_submit_button(
                "Generate Neuroref Cz Report"
            )

        if regenerate_neuroref or addendum:
            approved_eegs = edited_eeg_history_df[
                edited_eeg_history_df["include?"] == True
            ]
            asyncio.run(
                data_manager.update_neuroref_reports(
                    approved_eegs["EEGId"].values.tolist()
                )
            )
            st.rerun()

        if regenerate_neuroref_cz:
            approved_eegs = edited_eeg_history_df[
                edited_eeg_history_df["include?"] == True
            ]
            asyncio.run(
                data_manager.update_neuroref_cz_reports(
                    approved_eegs["EEGId"].values.tolist()
                )
            )
            st.rerun()


        st.divider()

        render_documents(data_manager)

        st.divider()

        render_artifact_distortions(data_manager)

        st.divider()

        render_abnormalities(data_manager)

        st.divider()

        render_eeg_history(data_manager)



with tab3:
    eeg_visualization_dashboard()

with tab4:
    ecg_visualization_dashboard()
