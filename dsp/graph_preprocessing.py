import numpy as np
import pandas as pd
import streamlit as st
from scipy.signal import find_peaks

from datetime import datetime


sensitivities = {
    "1 uV": 1.0,
    "2 uV": 2.0,
    "3 uV": 3.0,
    "5 uV": 5.0,
    "7 uV": 7.0,
    "10 uV": 10.0,
    "15 uV": 15.0,
    "20 uV": 20.0,
    "30 uV": 30.0,
    "50 uV": 50.0,
    "70 uV": 70.0,
    "100 uV": 100.0,
    "150 uV": 150.0,
    "200 uV": 200.0,
    "300 uV": 300.0,
    "500 uV": 500.0,
    "700 uV": 700.0,
    "1000 uV": 1000.0,
}



@st.cache_data
def scale_dataframe(df, sensitivity_slider=1.0, sensitivity_slider_uv=15.0):
    """
    Scale a dataframe with EEG (+EKG) channels so the default "sensitivity" for
    viewing results in readable activity. The scaling expects a channel offset of 1.

    Parameters:
    - df: pandas.core.frame.DataFrame
        Containing channel names with their channel data.

    Returns:
    - scaled_df: pandas.core.frame.DataFrame
        The same df just scaled to be readable for an offest between channels of 1.
    """

    # separate the 'Time' column
    try:
        times_col = df["time"]
    except:
        pass
    try:
        timestamps_col = df["timestamp"]
    except:
        pass

    # identify ECG and EEG columns
    try:
        ecg_columns = df.filter(like="ECG").columns
        eeg_columns = df.columns.difference(ecg_columns).difference(
            ["time", "timestamp"]
        )
    except:
        eeg_columns = df.columns

    # function to find local maxima and minima
    def find_extrema(signal):
        peaks, _ = find_peaks(signal)
        troughs, _ = find_peaks(-signal)
        return peaks, troughs

    # Function to return min/max stats for the eeg based on peaks and troughs
    def get_min_max_stats(columns, df):
        # calculate the median of maxima and minima for each EEG channel
        median_max_values = []
        median_min_values = []
        mean_max_values = []
        mean_min_values = []

        # get the peaks and the troughs
        for col in columns:
            peaks, troughs = find_extrema(df[col])
            max_values = df[col].iloc[peaks]
            min_values = df[col].iloc[troughs]
            if len(max_values) > 0:
                median_max_values.append(max_values.median())
                mean_max_values.append(max_values.mean())
            if len(min_values) > 0:
                median_min_values.append(min_values.median())
                mean_min_values.append(min_values.mean())

        # calculate the max of the above 0 median peaks and the min of the below 0 median troughs
        median_max = np.max(median_max_values)
        median_min = np.min(median_min_values)
        mean_max = np.max(mean_max_values)
        mean_min = np.min(mean_min_values)

        return median_max, median_min, mean_max, mean_min

    median_max, median_min, mean_max, mean_min = get_min_max_stats(eeg_columns, df)

    # scale the EEG columns
    df_eeg = df[eeg_columns]

    # new norm: scale to -1, 1 and then adjust it to a percentage of so clean waveforms
    #   arent reaching the bound (on average)
    bound = (median_max + abs(median_min)) / 2
    # scaled_eeg = (df_eeg / bound) * 0.25 * sensitivity_slider ###

    # DODS-99 -->
    scaled_eeg = (df_eeg / float(sensitivity_slider_uv)) * 0.1


    try:
        # scale ECG column(s) separately
        median_max, median_min, mean_max, mean_min = get_min_max_stats(ecg_columns, df)

        df_ecg = df[ecg_columns]

        # new norm: scale to -1, 1 and then adjust it to a percentage of
        bound = (median_max + abs(median_min)) / 2
        scaled_ecg = (df_ecg / bound) * 0.05 * sensitivity_slider ###

        # reattach the 'time' column and combine scaled columns
        try:
            scaled_df = pd.concat(
                [times_col, timestamps_col, scaled_ecg, scaled_eeg], axis=1
            )
        except:
            scaled_df = pd.concat([times_col, scaled_ecg, scaled_eeg], axis=1)

    except:
        # reattach the 'time' column and combine scaled columns
        try:
            scaled_df = pd.concat([times_col, timestamps_col, scaled_eeg], axis=1)
        except:
            scaled_df = pd.concat([times_col, scaled_eeg], axis=1)

    return scaled_df