"""Parse MyWavePlatform Abnormality API response for application"""

import numpy as np
import pandas as pd
import streamlit as st

from utils.helpers import format_single


def serialize_ahr_to_pandas(predictions, confidence_threshold=0.9, epoch_length=0.7):
    # Extract the probabilities array from the dictionary
    probabilities = predictions["predictions"]
    r_peaks = predictions["r_peaks"]

    # Initialize lists to store the data
    onsets = []
    confidences = []
    is_arrhythmia = []

    # Iterate through the probabilities to find values above the threshold
    for index, probability in enumerate(probabilities):
        if probability > confidence_threshold:
            onsets.append(r_peaks[index])
            confidences.append(probability)
            is_arrhythmia.append(True)
        else:
            # Append data for all lists even if they do not meet the threshold
            onsets.append(r_peaks[index])
            confidences.append(probability)
            is_arrhythmia.append(False)

    # Create a DataFrame with the collected data
    df = pd.DataFrame(
        {"onsets": onsets, "probability": confidences, "is_arrhythmia": is_arrhythmia}
    )

    df["ahr_times"] = df["onsets"].apply(format_single)

    eeg_id = st.session_state.get("eeg_id", None)

    if eeg_id:
        df["eegid"] = eeg_id

    return df


def serialize_aea_to_pandas(
    predictions, confidence_threshold=0.75, epoch_length=2, ref="N/A"
):
    # Extract the probabilities array from the dictionary
    probabilities = predictions["predictions"]

    # Initialize lists to store the data
    onsets = []
    confidences = []
    is_seizure = []

    # Iterate through the probabilities to find values above the threshold
    for index, probability in enumerate(probabilities):
        if probability > confidence_threshold:
            onsets.append(index * epoch_length)
            confidences.append(probability)
            is_seizure.append(True)

        else:
            # Append data for all lists even if they do not meet the threshold
            onsets.append(index * epoch_length)
            confidences.append(probability)
            is_seizure.append(False)

    # Create a DataFrame with the collected data
    df = pd.DataFrame(
        {"onsets": onsets, "probability": confidences, "is_seizure": is_seizure}
    )
    df["montage"] = ref

    df["aea_times"] = df["onsets"].apply(format_single)

    eeg_id = st.session_state.get("eeg_id", None)

    if eeg_id:
        df["eegid"] = eeg_id

    return df


def serialize_autoreject_to_pandas(json_data, epoch_length=2.56):
    # Extract the probabilities array from the dictionary
    bad_epochs = np.array(json_data["bad_epochs"])

    bad_epoch_onsets = np.where(bad_epochs == True)[0] * epoch_length

    # Create a DataFrame with the collected data
    df = pd.DataFrame({"onsets": bad_epoch_onsets.tolist()})

    return df
