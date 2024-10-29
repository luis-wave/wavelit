import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from mywaveanalytics.utils.params import (CHANNEL_ORDER_BIPOLAR_LONGITUDINAL,
                                          CHANNEL_ORDER_TEMPORAL_CENTRAL_PARASAGITTAL,
                                          CHANNEL_ORDER_PERSYST)


# Plotly figure creation
def draw_eeg_graph(df, ref, offset_value=1.0):
    fig = go.Figure()

    # Define the order of channels based on reference
    if ref in ["linked_ears", "centroid"]:
        ordered_channels = CHANNEL_ORDER_PERSYST[:-2][::-1]
    elif ref in ["bipolar_longitudinal"]:
        # ordered_channels = CHANNEL_ORDER_BIPOLAR_LONGITUDINAL
        ordered_channels = CHANNEL_ORDER_TEMPORAL_CENTRAL_PARASAGITTAL

    df["time"] = pd.to_datetime(df["time"], unit="s")

    # Add traces to fig
    for i, channel in enumerate(ordered_channels):
        offset = i * offset_value
        fig.add_trace(
            go.Scattergl(
                x=df["time"],
                y=df[channel] + offset,
                mode="lines+markers",
                name=channel,
                line=dict(
                    color="#4E4E4E",
                    width=0.8,
                ),
                marker=dict(
                    size=2,
                    opacity=0.01,
                    color="#4E4E4E", # dark purple
                ),
            )
        )

    # Use a form to contain the data editor and submit button
    # Retrieve ahr from session state
    aea = st.session_state.get("aea", None)

    if aea is not None:
        if not aea[ref].empty:
            abnormal_epochs = st.session_state.aea[ref][
                st.session_state.aea[ref]["is_seizure"] == True
            ]["onsets"]
            for onset in abnormal_epochs:
                fig.add_shape(
                    # adding a Rectangle for seizure epoch
                    type="rect",
                    x0=pd.to_datetime(onset, unit="s"),  # start time of seizure
                    x1=pd.to_datetime(
                        onset + 2, unit="s"
                    ),  # end time of seizure (2 seconds after start)
                    y0=-150,  # start y (adjust according to your scale)
                    y1=offset * len(ordered_channels),  # end y
                    fillcolor="#7e35ac",  # color of the shaded area, og: "#FF7373"
                    opacity=0.1,  # transparency, og: 0.9
                    layer="below",  # draw below the data
                    line_width=0,
                )

    autoreject = st.session_state.get("autoreject", None)

    if autoreject is not None:
        if ref != "bipolar_longitudinal":
            if not autoreject[ref].empty:
                bad_epochs = st.session_state.autoreject[ref]["onsets"]
                for onset in bad_epochs:
                    fig.add_shape(
                        # adding a Rectangle for seizure epoch
                        type="rect",
                        x0=pd.to_datetime(onset, unit="s"),  # start time of seizure
                        x1=pd.to_datetime(
                            onset + 2.56, unit="s"
                        ),  # end time of seizure (2 seconds after start)
                        y0=-150,  # start y (adjust according to your scale)
                        y1=offset * len(ordered_channels),  # end y
                        fillcolor="#355cac",  # color of the shaded area, og: #5ad1ad
                        opacity=0.1,  # transparency
                        layer="below",  # draw below the data
                        line_width=0,
                    )

    # Create custom y-axis tick labels and positions
    yticks = [i * offset_value for i in range(len(ordered_channels))]
    ytick_labels = ordered_channels

    filename = st.session_state.get("fname", "EEG Visualization")

    fig.update_layout(
        title=st.session_state.recording_date,
        xaxis_title="",
        yaxis_title="",
        xaxis={
            "rangeslider": {"visible": True,
                            "thickness": 0.06,
                            },
            "range": [
                df["time"].iloc[0],
                df["time"].iloc[0] + pd.Timedelta(seconds=20),
            ],
            "tickformat": "%M:%S.%L",
            "showgrid": True,
            "gridcolor": "#bdbdbd",
            "dtick": 1000,
            "zeroline": False,
        },
        yaxis={
            "tickvals": yticks,
            "ticktext": ytick_labels,
            "tickmode": "array",
            "range": [(-1.5), (max(yticks) + offset_value+0.5)],
            "showgrid": False,
            "zeroline": False,
        },
        legend=dict(
            traceorder="reversed",
            # itemsizing='constant'
            ),
        height=800,
        margin=dict(t=20,l=0,r=0,b=5),
    )
    return fig
