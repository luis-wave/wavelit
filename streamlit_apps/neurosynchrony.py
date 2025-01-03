"""
Set up the primary UI for eeg report and protocol review.
"""

import asyncio
import logging

import streamlit as st
import streamlit.components.v1 as components
from streamlit_pdf_viewer import pdf_viewer

from access_control import access_eeg_data
from services.mert2_data_management.mert_data_manager import MeRTDataManager
from streamlit_apps.mert_components import (render_abnormalities,
                                            render_artifact_distortions,
                                            render_documents,
                                            render_eeg_review, render_notes,
                                            render_protocol_page)
from streamlit_dashboards import eeg_visualization_dashboard
from streamlit_dashboards import ecg_visualization_dashboard

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


data_manager = None

if (
    ("eegid" in st.session_state)
    and ("pid" in st.session_state)
    and ("clinicid" in st.session_state)
):
    # Initialize MeRTDataManager
    data_manager = MeRTDataManager(
        patient_id=st.session_state["pid"],
        eeg_id=st.session_state["eegid"],
        clinic_id=st.session_state["clinicid"],
    )

    # Load all data into session state
    asyncio.run(data_manager.load_all_data())


def delete_report(data_manager, report_id, ref="default"):
    if ref == "default":
        asyncio.run(data_manager.delete_neuroref_report(report_id))
        st.success(f"Neuroref {report_id} successfully deleted!")
        st.rerun()
    elif ref == "cz":
        asyncio.run(data_manager.delete_neuroref_cz_report(report_id))
        st.success(f"Neuroref Cz {report_id} successfully deleted!")
        st.rerun()


tabs = ["Reports", "Protocols", "EEG", "ECG"]

tab1, tab2, tab3, tab4 = st.tabs(tabs)

with tab1:
    # Start rendering the UI
    st.title("NeuroSynchrony Review")

    col1, col2 = st.columns(2)

    with col1:
        patient_data = st.session_state.patient_data
        clinic_info = st.session_state.clinic_info

        first_name = patient_data["profileInfo"]["name"]["first"]
        last_name = patient_data["profileInfo"]["name"]["last"]
        middle_name = patient_data["profileInfo"]["name"]["middle"]
        username = patient_data["profileInfo"]["username"]
        dob = patient_data["profileInfo"]["dateOfBirth"]
        sex = patient_data["profileInfo"]["sex"].capitalize()
        patient_id = patient_data["profileInfo"]["patientId"]
        primary_complaint = patient_data["clinicalInfo"]["primaryComplaint"]
        is_having_seizures = (
            "Yes" if patient_data["clinicalInfo"]["isHavingSeizures"] else "No"
        )

        if "CORTICAL" in st.session_state.treatment_count:
            treatment_count = st.session_state.treatment_count["CORTICAL"]
        else:
            treatment_count = 0

        # Display patient data
        st.header(f"{first_name} {middle_name + ' ' if middle_name else ''}{last_name}")
        st.markdown(f"Username: **{username}**")
        st.markdown(f"Sex: **{sex}**")
        st.markdown(f"DOB: **{dob}**")
        st.markdown(f"Seizure History: **{is_having_seizures}**")
        st.markdown(f"Treatment Session Count: **{treatment_count}**")
        st.markdown(f"PatientId: **{patient_id}**")
        st.markdown(f"Primary Chief Complaint: **{primary_complaint}**")

        st.divider()

        # Clinic info
        st.subheader(clinic_info["name"])
        st.markdown(f"ClinicId: **{clinic_info['clinicId']}**")
        st.markdown(f"Phone number: **{clinic_info['phone']}**")
        st.markdown(f"City: **{clinic_info['address']['city']}**")
        st.markdown(f"State: **{clinic_info['address']['state']}**")
        st.markdown(f"Country: **{clinic_info['address']['country']}**")

    if "eegScientistPatientNotes" in patient_data:
        eeg_scientist_patient_notes = patient_data["eegScientistPatientNotes"]
    else:
        eeg_scientist_patient_notes = None

    render_notes(data_manager, eeg_scientist_patient_notes)

    with col2:
        render_eeg_review(data_manager)
        eeg_history_df = st.session_state.eeg_history

        with st.popover("Generate report"):
            st.header("EEG History")
            with st.form("data_editor_form", border=False):
                edited_eeg_history_df = st.data_editor(eeg_history_df, hide_index=True)
                regenerate_neuroref = st.form_submit_button("Generate Neuroref Report")
                regenerate_neuroref_cz = st.form_submit_button(
                    "Generate Neuroref Cz Report"
                )

            if regenerate_neuroref:
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

        st.subheader("Reports")
        if "downloaded_neuroref_report" in st.session_state:
            for idx, report_data in enumerate(
                st.session_state.downloaded_neuroref_report
            ):
                report, report_id = report_data
                with st.expander(label=f"Neurosynchrony - Linked Ears {report_id}", expander=True):
                    pdf_viewer(report, height=700, key=f"linked_ears {idx}")
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
                with st.expander(label=f"Neurosynchrony - Centroid {report_id}", expander=True):
                    pdf_viewer(report, height=700, key=f"centroid {idx}")
                    st.download_button(
                        label="Download Neuroref Cz",
                        data=report,
                        file_name=f"Neurosynchrony-Cz-{report_id}.pdf",
                        key=f"download-cz-{report_id}",
                    )
                    if st.button(label="Delete", key=f"Neurosynchrony-cz-{report_id}"):
                        delete_report(data_manager, report_id, ref="cz")
                        st.success(f"Neuroref Cz {report_id} successfully deleted!")

        render_documents(data_manager)

        render_artifact_distortions(data_manager)

        render_abnormalities(data_manager)


with tab2:
    render_protocol_page(data_manager)
    st.title("Protocol Queue")
    html = f'<iframe src="https://app.sigmacomputing.com/embed/1-7DtFiDy0cUmAAIztlEecY5" frameborder="0" width="100%" height="900px"></iframe>'
    components.html(html, height=1000, scrolling=False)

with tab3:
    asyncio.run(access_eeg_data(st.session_state["eegid"]))
    eeg_visualization_dashboard()

with tab4:
    asyncio.run(access_eeg_data(st.session_state["eegid"]))
    ecg_visualization_dashboard()