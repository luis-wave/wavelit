import asyncio
import streamlit as st
import streamlit_shadcn_ui as ui

from .review_utils import EEGReviewState, get_next_state, mert2_user
from utils.helpers import format_datetime

REJECTION_REASONS = {
    "possibleDrowsiness": "Possible Drowsiness",
    "excessiveArtifact": "Excessive Artifact",
    "poorEegSetup": "Poor EEG Setup",
    "incorrectUpload": "Incorrect Upload",
    "other": "Other",
}



def get_eeg_info(data_manager):
    return asyncio.run(data_manager.fetch_eeg_info_by_patient_id_and_eeg_id())

def handle_approve(data_manager, current_state):
    next_state = get_next_state(current_state)
    try:
        asyncio.run(
            data_manager.update_eeg_review(
                is_first_reviewer=(current_state == EEGReviewState.PENDING),
                state=next_state.name,
            )
        )
        st.session_state.needs_refresh = True
        st.success(f"Review updated to {next_state.name.replace('_', ' ')}")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to update review: {str(e)}")

def handle_reject(data_manager, current_state, reasons):
    if not reasons:
        st.error("Please select at least one rejection reason.")
        return
    try:
        asyncio.run(
            data_manager.update_eeg_review(
                is_first_reviewer=(current_state == EEGReviewState.PENDING),
                state=EEGReviewState.REJECTED.name,
                rejection_reason=reasons,
            )
        )
        st.session_state.needs_refresh = True
        st.success("Review rejected successfully.")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to reject review: {str(e)}")


@st.fragment
def render_eeg_review(data_manager):
    """Render the EEG review UI with explicit and clean structure."""
    if 'needs_refresh' not in st.session_state:
        st.session_state.needs_refresh = False

    eeg_info = get_eeg_info(data_manager)
    analysis_meta = eeg_info["eegInfo"]["analysisMeta"]

    current_state = (
        EEGReviewState[analysis_meta["reviewState"]]
        if analysis_meta["reviewState"]
        else EEGReviewState.PENDING
    )

    first_reviewer = mert2_user.get(analysis_meta.get("reviewerStaffId"), "N/A")
    second_reviewer = mert2_user.get(analysis_meta.get("secondReviewerStaffId"), "N/A")

    current_state_name = current_state.name.replace('_', ' ')

    # Main Review Card
    with ui.card(key="eeg_review"):
        # Header Section
        ui.element("h3", children=["EEG Review Status"], className="text-xl font-bold mb-4", key="header_title")

        if current_state_name != 'REJECTED':
            ui.element("div", children=[f"Status: {current_state_name}"],
                    className="bg-blue-500 text-white px-4 py-2 rounded-full inline-block mb-6", key="header_status")
        else:
            ui.element("div", children=[f"Status: {current_state_name}"],
                   className="bg-red-500 text-white px-4 py-2 rounded-full inline-block mb-6", key="header_status")

        # First Review Section
        ui.element("h4", children=["First Review"], className="text-lg font-semibold mb-2", key="first_review_title")
        ui.element("span", children=["Review Date:"], className="text-gray-500 text-sm font-medium", key="first_review_date_label")
        ui.element("div", children=[format_datetime(analysis_meta.get('reviewDatetime'))], className="mb-2", key="first_review_date")
        ui.element("span", children=["Reviewer:"], className="text-gray-500 text-sm font-medium", key="first_reviewer_label")
        ui.element("div", children=[first_reviewer], className="mb-4", key="first_reviewer_value")

        # Divider
        ui.element("hr", className="my-4", key="divider1")

        # Second Review Section
        ui.element("h4", children=["Second Review"], className="text-lg font-semibold mb-2", key="second_review_title")
        ui.element("span", children=["Review Date:"], className="text-gray-500 text-sm font-medium", key="second_review_date_label")
        ui.element("div", children=[format_datetime(analysis_meta.get('secondReviewDatetime'))], className="mb-2", key="second_review_date")
        ui.element("span", children=["Reviewer:"], className="text-gray-500 text-sm font-medium", key="second_reviewer_label")
        ui.element("div", children=[second_reviewer], className="mb-4", key="second_reviewer_value")

    # Actions Section
    can_review = st.session_state["id"] not in [
        analysis_meta.get("reviewerStaffId"),
        analysis_meta.get("secondReviewerStaffId"),
    ]

    if (can_review and current_state != EEGReviewState.REJECTED and current_state != EEGReviewState.CLINIC_REVIEW and EEGReviewState.COMPLETED):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Approve Review", type="primary", key="approve_btn"):
                handle_approve(data_manager, current_state)

        with col2:
            with st.form(key="reject_form", clear_on_submit=True):
                selected_reasons = st.multiselect(
                    "Select Rejection Reasons",
                    options=list(REJECTION_REASONS.keys()),
                    format_func=lambda x: REJECTION_REASONS[x]
                )
                if st.form_submit_button("Reject Review"):
                    handle_reject(data_manager, current_state, selected_reasons)

def get_report_addendum_eeg_id(data_manager):
    return asyncio.run(data_manager.add_report_addendum())
