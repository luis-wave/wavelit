"""
Facilitates EEG review states. If an eeg report is approved in Streamlit, the eeg state is reflected back in MeRT 2.
"""

import asyncio
from enum import Enum

import streamlit as st

mert2_user = {
    "STF-e465eb68-ba87-11eb-8611-06b700432873": "Luis Camargo",
    "STF-6d38ac86-ba89-11eb-8b42-029e69ddbc8b": "Alex Ring",
    "STF-ac677ad4-a595-11ec-82d9-02fd9bf033d7": "Stephanie Llaga",
    "STF-e8b6c0a2-27f5-11ed-b837-02b0e344b06f": "Patrick Polk",
    "STF-934d6632-a17e-11ec-b364-0aa26dca46cb": "Joseph Chong",
    "STF-031845e2-b505-11ec-8b5d-0a86265d54df": "Nicole Yu",
    "STF-d844feb2-241c-11ef-8e46-02fb253d52c7": "Binh Le",
    "STF-7a0aa2d4-241c-11ef-a5ac-06026d518b71": "Rey Mendoza",
    "STF-0710bc38-2e40-11ed-a807-027d8017651d": "Jay Kumar",
    "STF-472808de-ba89-11eb-967d-029e69ddbc8b": "Jijeong Kim",
    "STF-143c1a12-8657-11ef-8e6a-020ab1ebdc67": "Uma Gokhale",
    "STF-8b4db98a-8657-11ef-9d8b-020ab1ebdc67": "Uma Gokhale2",
}


class EEGReviewState(Enum):
    PENDING = 0
    FIRST_REVIEW = 1
    SECOND_REVIEW_NEEDED = 2
    SECOND_REVIEW = 3
    CLINIC_REVIEW = 4
    COMPLETED = 6
    REJECTED = 7


REJECTION_REASONS = {
    "possibleDrowsiness": "Possible Drowsiness",
    "excessiveArtifact": "Excessive Artifact",
    "poorEegSetup": "Poor EEG Setup",
    "incorrectUpload": "Incorrect Upload",
    "other": "Other",
}


def get_next_state(current_state: EEGReviewState) -> EEGReviewState:
    state_order = [
        EEGReviewState.PENDING,
        EEGReviewState.FIRST_REVIEW,
        EEGReviewState.SECOND_REVIEW,
        EEGReviewState.COMPLETED,
    ]
    try:
        current_index = state_order.index(current_state)
        return (
            state_order[current_index + 1]
            if current_index < len(state_order) - 1
            else current_state
        )
    except ValueError:
        return current_state


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
