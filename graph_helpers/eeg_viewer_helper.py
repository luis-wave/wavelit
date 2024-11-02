import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime

from mywaveanalytics.utils.params import (CHANNEL_ORDER_BIPOLAR_LONGITUDINAL,
                                          CHANNEL_ORDER_TEMPORAL_CENTRAL_PARASAGITTAL,
                                          CHANNEL_ORDER_PERSYST)


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
    
    def convert_timestamp(timestamp):
        # Parse the input timestamp
        timestamp = timestamp.split(" ", 1)[1] if " " in timestamp else timestamp
        
        try: 
            dt = datetime.strptime(timestamp, "%H:%M:%S.%f")
        except:
            dt = datetime.strptime(timestamp, "%H:%M:%S")
        
        # Format as MM:SS
        formatted_time = dt.strftime("%M:%S")
        return formatted_time
    

    if "current_montage" not in st.session_state:
        st.session_state.current_montage = "linked ears"

    # Define the order of channels based on reference
    if st.session_state.current_montage in ["linked_ears", "centroid"]:
        ordered_channels = CHANNEL_ORDER_PERSYST[:-2][::-1]
    elif st.session_state.current_montage in ["bipolar_longitudinal"]:
        # ordered_channels = CHANNEL_ORDER_BIPOLAR_LONGITUDINAL
        ordered_channels = CHANNEL_ORDER_TEMPORAL_CENTRAL_PARASAGITTAL

    onsets = select_event["selection"].get("points", None)
    # Create a list with each row in the specified order
    selection_list = [
        [
            convert_timestamp(point['x']),
            ordered_channels[point['curve_number']],
            st.session_state.ref_selectbox,
            point['x'],     
            st.session_state.user,

        ]
        for i, point in enumerate(onsets)
    ]
    
    return selection_list



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
    
    for row in row_list:
        if row not in df_as_list:
            df_as_list.append(row)
    
    # Convert the combined list back to a DataFrame with the original columns
    combined_df = pd.DataFrame(df_as_list, columns=df.columns)

    if sort:
        combined_df = combined_df.sort_values(by=['x'], ascending=[True])
        combined_df = combined_df.reset_index(drop=True)
    
    return combined_df