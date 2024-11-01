import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime


def event_to_list(select_event):
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
    
    
    onsets = select_event["selection"].get("points", None)
    # Create a list with each row in the specified order
    selection_list = [
        [
            convert_timestamp(point['x']),  # x value
            point['curve_number'],          # curve number
            point['point_index']            # point index
        ]
        for i, point in enumerate(onsets)
    ]
    
    return selection_list




def add_list_to_df(df, row_list, sort=True):

    # Convert the DataFrame to a list of lists
    df_as_list = df.values.tolist()
    
    for row in row_list:
        if row not in df_as_list:
            df_as_list.append(row)
    
    # Convert the combined list back to a DataFrame with the original columns
    combined_df = pd.DataFrame(df_as_list, columns=df.columns)

    if sort:
        combined_df.sort_values(by=['x', 'curve_number'], ascending=[True, True])
        combined_df = combined_df.reset_index(drop=True)
    
    return combined_df