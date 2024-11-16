import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta


def event_to_list(select_event=None, ordered_channels=None):
    """
    Takes a plotly selection event and turns it into a formatted list 
    of data for each onset.

    Parameters:
    - select_event: pandas.core.frame.DataFrame
        Selection data from plotly chart.
    - ordered_channels: class 'list'
        A list of channels for the montage.

    Returns:
    - selection_list: class 'list'
        A formatted list of data from the selection/click event.
    """

    if "current_montage" not in st.session_state:
        st.session_state.current_montage = "linked ears"

    onsets = select_event["selection"].get("points", [])
    aea = st.session_state.get("aea", None)

    if aea is not None and not aea[st.session_state.current_montage].empty:
        aea_df = aea[st.session_state.current_montage].copy()
         
        # Create a list with each row in the specified order
        selection_list = [
            [
                convert_point_to_timestamp(point["x"]),
                point["x"],
                float_to_full_timestamp(point["x"]),
                get_probability(point["x"], aea_df),
                ordered_channels[point["curve_number"]],
                st.session_state.ref_selectbox,
                "",
                st.session_state.user,
            ]
            for i, point in enumerate(onsets)
        ]
    else:
        # Create a list with each row in the specified order
        selection_list = [
            [
                convert_point_to_timestamp(point["x"]),
                point["x"],
                float_to_full_timestamp(point["x"]),
                0.0, # Since no ML AEA onsets provided
                ordered_channels[point["curve_number"]],
                st.session_state.ref_selectbox,
                "",
                st.session_state.user,
            ]
            for i, point in enumerate(onsets)
        ]

    return selection_list


def convert_point_to_timestamp(point):
    """
    Take in the clicked x point and convert it to a MM:SS value.

    Parameters:
    - point: float
        The selected point value.

    Returns:
    - formatted_time: string
        A timestamp represented by a MM:SS value.
    """
    if isinstance(point, int):
        formatted_time = float_to_minute_timestamp(float(point))
    elif isinstance(point, float):
        formatted_time = float_to_minute_timestamp(point)
    else:
        # For pandas datetime selection points
        try:
            # Parse the x point from the plotly selection event to get the time only
            timestamp = point.split(" ", 1)[1] if " " in point else point

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


def get_probability(point, aea_df=None):
    """
    Finds the probability that the selected point from the plotly graph is AEA by
    referencing the machine learning AEA df. Odd numbered point values as of 
    11/14/2024 dont have probabilities, so they are given a probability of zero. 

    Parameters:
    - point: float
        The selected point value.
    - aea_df: pandas.core.frame.DataFrame
        Dataframe of AEA machine learning data for even numbered onsets of an EEG.

    Returns:
    - probability: float
        The probability determined by the ML model that the onset contains AEA.
    """

    if isinstance(point, int):
        timestamp = float_to_minute_timestamp(float(point))
        timestamp = "00:" + timestamp + ".000"
    elif isinstance(point, float):
        timestamp = float_to_minute_timestamp(point)
        timestamp = "00:" + timestamp + ".000"
    else:
        # Parse the input timestamp
        timestamp = point.split(" ", 1)[1] if " " in point else point

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
    channel_column = [row[3] for row in df_as_list]
    for row in row_list:
        if row[3] not in channel_column:
            df_as_list.append(row)
        elif row[0] not in onset_column:
            df_as_list.append(row)

    # Convert the combined list back to a DataFrame with the original columns
    combined_df = pd.DataFrame(df_as_list, columns=df.columns)

    if sort:
        combined_df = combined_df.sort_values(by=["x"], ascending=[True])
        combined_df = combined_df.reset_index(drop=True)

    return combined_df


def float_to_full_timestamp(seconds):
    # Create a timedelta from seconds
    td = timedelta(seconds=seconds)
    # Get total hours, minutes, and seconds
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

def float_to_minute_timestamp(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes:02}:{remaining_seconds:02}"

def round_down_millis(timestamp):
    try: 
        # Split the timestamp at the dot to separate the minutes/seconds from milliseconds
        time_part, _ = timestamp.split(".")

        # Append '.000' to get the desired format
        return f"{time_part}.000"
    except Exception as e:
        print("CHECK IF TIMESTAMP HAS MILLISECOND VALUE")
        print(e)