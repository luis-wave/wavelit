from enum import Enum

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


def get_next_state(current_state: EEGReviewState) -> EEGReviewState:
    state_order = [
        EEGReviewState.PENDING,
        EEGReviewState.SECOND_REVIEW_NEEDED,
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
