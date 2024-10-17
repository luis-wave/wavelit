"""
Facilitates EEG review states. If an eeg report is approved in Streamlit, the eeg state is reflected back in MeRT 2.
"""

import asyncio

import streamlit as st

from .review_utils import EEGReviewState, get_next_state, mert2_user

REJECTION_REASONS = {
    "possibleDrowsiness": "Possible Drowsiness",
    "excessiveArtifact": "Excessive Artifact",
    "poorEegSetup": "Poor EEG Setup",
    "incorrectUpload": "Incorrect Upload",
    "other": "Other",
}


@st.fragment
def render_eeg_review(data_manager):
    st.markdown("## EEG Review")

    # Fetch EEG info
    eeg_info = asyncio.run(data_manager.fetch_eeg_info_by_patient_id_and_eeg_id())
    analysis_meta = eeg_info["eegInfo"]["analysisMeta"]

    current_state = (
        EEGReviewState[analysis_meta["reviewState"]]
        if analysis_meta["reviewState"]
        else EEGReviewState.PENDING
    )

    if analysis_meta and "reviewerStaffId" in analysis_meta:
        first_reviewer = mert2_user.get(analysis_meta["reviewerStaffId"], "N/A")
    else:
        first_reviewer = "N/A"

    if analysis_meta and "secondReviewerStaffId" in analysis_meta:
        second_reviewer = mert2_user.get(analysis_meta["secondReviewerStaffId"], "N/A")
    else:
        second_reviewer = "N/A"

    if current_state == EEGReviewState.REJECTED:
        st.markdown("### Rejected")
        st.markdown(f"**Review Date:** {analysis_meta['rejectionDatetime']}")
        st.markdown(
            f"**Rejected by:** {mert2_user[analysis_meta['rejectionReviewerStaffId']]}"
        )
        st.markdown("**Rejection Reason(s):**")
        for i in analysis_meta["rejectionReason"]:
            st.write(REJECTION_REASONS[i])
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### First Review")
            st.markdown(
                f"**Review Date:** {analysis_meta['reviewDatetime'] or 'Not reviewed yet'}"
            )
            st.markdown(f"**Approved By:** {first_reviewer}")

        with col2:
            st.markdown("### Second Review")
            st.markdown(
                f"**Review Date:** {analysis_meta['secondReviewDatetime'] or 'Not reviewed yet'}"
            )
            st.markdown(f"**Approved By:** {second_reviewer}")

    st.markdown(f"**Current State:** {current_state.name}")

    # Check if the current user can perform a review
    can_review = st.session_state["id"] not in [
        analysis_meta["reviewerStaffId"],
        analysis_meta["secondReviewerStaffId"],
    ]

    if can_review:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Proceed Review"):
                next_state = get_next_state(current_state)
                try:
                    asyncio.run(
                        data_manager.update_eeg_review(
                            is_first_reviewer=(current_state == EEGReviewState.PENDING),
                            state=next_state.name,
                        )
                    )
                    st.success(f"Review updated to {next_state.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update review: {str(e)}")

        with col2:
            with st.form(key="reject_form"):
                st.markdown("### Reject Review")
                rejection_reasons = st.multiselect(
                    "Select Rejection Reasons",
                    options=list(REJECTION_REASONS.keys()),
                    format_func=lambda x: REJECTION_REASONS[x],
                )
                reject_button = st.form_submit_button(label="Reject Review")

                if reject_button:
                    if not rejection_reasons:
                        st.error("Please select at least one rejection reason.")
                    else:
                        try:
                            asyncio.run(
                                data_manager.update_eeg_review(
                                    is_first_reviewer=(
                                        current_state == EEGReviewState.PENDING
                                    ),
                                    state=EEGReviewState.REJECTED.name,
                                    rejection_reason=rejection_reasons,
                                )
                            )
                            st.success("Review rejected.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to reject review: {str(e)}")
