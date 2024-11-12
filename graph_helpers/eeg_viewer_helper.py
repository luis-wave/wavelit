import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

from mywaveanalytics.utils.params import (
    CHANNEL_ORDER_BIPOLAR_LONGITUDINAL,
    CHANNEL_ORDER_TEMPORAL_CENTRAL_PARASAGITTAL,
    CHANNEL_ORDER_PERSYST,
)


def event_to_list(select_event=None):
    """
    Takes a plotly click event and turns it into a formatted list.
    Formats the clicked timestamp to an onset in MM:SS.

    Parameters:
    - select_event: pandas.core.frame.DataFrame
        Selection data from plotly chart.

    Returns:
    - selection_list: class 'list'
        A formatted list of data from the click event.
    """

    if "current_montage" not in st.session_state:
        st.session_state.current_montage = "linked ears"

    # Define the order of channels based on reference
    if st.session_state.current_montage in ["linked_ears", "centroid"]:
        ordered_channels = CHANNEL_ORDER_PERSYST[:-2][::-1]
    elif st.session_state.current_montage in ["bipolar_longitudinal"]:
        # ordered_channels = CHANNEL_ORDER_BIPOLAR_LONGITUDINAL
        ordered_channels = CHANNEL_ORDER_TEMPORAL_CENTRAL_PARASAGITTAL

    onsets = select_event["selection"].get("points", None)
    aea_df = st.session_state.aea[st.session_state.current_montage].copy()

    # Create a list with each row in the specified order
    selection_list = [
        [
            convert_timestamp(point["x"]),
            get_probability(point, aea_df),
            ordered_channels[point["curve_number"]],
            st.session_state.ref_selectbox,
            convert_seconds_to_hhmmss(point["x"]),
            st.session_state.user,
        ]
        for i, point in enumerate(onsets)
    ]

    return selection_list


def convert_seconds_to_hhmmss(seconds):
    # Create a timedelta from seconds
    td = timedelta(seconds=seconds)
    # Get total hours, minutes, and seconds
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"


def float_to_timestamp(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes:02}:{remaining_seconds:02}"


def convert_timestamp(timestamp):
    if isinstance(timestamp, float):
        formatted_time = float_to_timestamp(timestamp)
    else:
        try: 
            # Parse the input timestamp
            timestamp = timestamp.split(" ", 1)[1] if " " in timestamp else timestamp

            try:
                dt = datetime.strptime(timestamp, "%H:%M:%S.%f")
            except:
                dt = datetime.strptime(timestamp, "%H:%M:%S")

            # Format as MM:SS
            formatted_time = dt.strftime("%M:%S")
        except Exception as e:
            print(f"CLICKED ONSET: {timestamp} of type: {type(timestamp)}")
            print(e)


    return formatted_time


def round_down_millis(timestamp):
    # Split the timestamp at the dot to separate the minutes/seconds from milliseconds
    time_part, _ = timestamp.split(".")

    # Append '.000' to get the desired format
    return f"{time_part}.000"


def get_probability(point, aea_df=None):
    if isinstance(point["x"], float):
        timestamp = float_to_timestamp(point["x"])
        timestamp = "00:" + timestamp + ".000"
    else:
        # Parse the input timestamp
        timestamp = point["x"].split(" ", 1)[1] if " " in point["x"] else point["x"]

    # Convert to datetime
    dt = datetime.strptime(timestamp, "%H:%M:%S.%f")

    # Get new format and round
    formatted_time = round_down_millis(dt.strftime("%M:%S.%f"))

    # Get probability value for the given aea_times value
    probability = aea_df.loc[aea_df["aea_times"] == formatted_time, "probability"]

    # If there is no corresponding aea_times value, set probability to 0.0
    probability = probability.values[0] if not probability.empty else 0.0

    return probability


def add_list_to_df(df, row_list, sort=True):
    """
    Takes a list and adds it to a dataframe with the option to sort the new
    combined dataframe by the 'x' column

    Parameters:
    - df: pandas.core.frame.DataFrame
        The main dataframe that the list data will get added to.
    - row_list: class 'list'
        The passed in list to append to the passed in dataframe.
    - sort: boolean
        Whether or not to sort the new dataframe.

    Returns:
    - combined_df: pandas.core.frame.DataFrame
        The combined dataframe including the list's data that was passed in.
    """

    # Convert the DataFrame to a list of lists
    df_as_list = df.values.tolist()

    # Only add the selection if the onset 
    onset_column = [row[0] for row in df_as_list]
    channel_column = [row[2] for row in df_as_list]
    for row in row_list:
        if row[2] not in channel_column:
            df_as_list.append(row)
        elif row[0] not in onset_column:
            df_as_list.append(row)

    # Convert the combined list back to a DataFrame with the original columns
    combined_df = pd.DataFrame(df_as_list, columns=df.columns)

    if sort:
        combined_df = combined_df.sort_values(by=["x"], ascending=[True])
        combined_df = combined_df.reset_index(drop=True)

    return combined_df
