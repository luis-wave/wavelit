
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from mywaveanalytics.utils.params import CHANNEL_ORDER_EEG


# Plotly figure creation

@st.cache_data
def create_plotly_figure(df, channels, offset_value):
    fig = go.Figure()
    channels = channels[::-1]

    df['time'] = pd.to_datetime(df['time'], unit='s')

    for i, channel in enumerate(channels):
        offset = i * offset_value
        fig.add_trace(
            go.Scattergl(
                x=df['time'],
                y=df[channel] + offset,  # Apply vertical offset
                mode="lines",
                name=channel,
                line=dict(color='#4E4E4E'),
            )
        )

    seizure_epochs = pd.DataFrame()
    # Adding shaded regions for seizure activity
    # Initialize the DataFrame in the session state if it hasn't been initialized yet
    if 'data' not in st.session_state or st.session_state['data'] is None:
        st.session_state['data'] = pd.DataFrame()

        # Use a form to contain the data editor and submit button
    if not st.session_state.data.empty:
        seizure_epochs = st.session_state.data[st.session_state.data['is_seizure'] == True]['onsets']


    if seizure_epochs.any().any():
        for onset in seizure_epochs:
            fig.add_shape(
                # adding a Rectangle for seizure epoch
                type="rect",
                x0=pd.to_datetime(onset, unit='s'),  # start time of seizure
                x1=pd.to_datetime(onset + 2, unit='s'),  # end time of seizure (2 seconds after start)
                y0=-150,  # start y (adjust according to your scale)
                y1=offset * len(channels),  # end y
                fillcolor="#FF7373",  # color of the shaded area
                opacity=1,  # transparency
                layer="below",  # draw below the data
                line_width=0,
            )

    # Create custom y-axis tick labels and positions
    yticks = [i * offset_value for i in range(len(channels))]
    ytick_labels = channels

    filename = st.session_state.get('fname', 'EEG Visualization')


    fig.update_layout(
        title=st.session_state.recording_date,
        xaxis_title="Time",
        yaxis_title="EEG Channels",
        xaxis={"rangeslider": {"visible": True}, 'range': [df['time'].iloc[0], df['time'].iloc[0] + pd.Timedelta(seconds=20)], 'tickformat': '%M:%S.%L' },
        yaxis={
            "tickvals": yticks,
            "ticktext": ytick_labels,
            "tickmode": "array",
            "range": [-100, max(yticks) + offset_value]
        },
        height=1000,  # Consistent height
    )
    return fig