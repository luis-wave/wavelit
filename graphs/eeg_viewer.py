import pandas as pd
import datetime
import math

import plotly.graph_objects as go
import streamlit as st


def draw_eeg_graph(df, ref, channels, sfreq=50, offset_value=1.0):
    def format_seconds(seconds):
        # Convert seconds to timedelta
        td = datetime.timedelta(seconds=seconds)
        # Get minutes and seconds
        minutes, seconds = divmod(td.seconds, 60)
        # Extract milliseconds from timedelta
        milliseconds = td.microseconds // 1000
        return f"{minutes:02}:{seconds:02}"  # .{milliseconds:03}"

    # Create tick labels in desired format
    tick_vals = df[df["time"] % 1.0 == 0.0]["time"].values  # Original values in seconds
    tick_text = [format_seconds(x) for x in tick_vals]  # Formatted as MM:SS.SSS

    # Initialize fig object
    fig = go.Figure()

    # Add traces to fig
    for i, channel in enumerate(channels):
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
                    color="#4E4E4E",
                ),
            )
        )

    # Use a form to contain the data editor and submit button
    # Retrieve ahr from session state
    if st.session_state.highlight_ml_onsets:
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
                        x0=onset,  # start time of seizure
                        x1=onset + 2,  # end time of seizure (2 seconds after start)
                        y0=-150,  # start y (adjust according to your scale)
                        y1=offset * len(channels),  # end y
                        fillcolor="#FF7373",
                        opacity=0.2,  # transparency, og: 0.9
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
                        x0=onset,  # start time of seizure
                        x1=onset + 2,  # end time of seizure (2 seconds after start)
                        y0=-150,  # start y (adjust according to your scale)
                        y1=offset * len(channels),  # end y
                        fillcolor="#355cac",  # color of the shaded area, og: #5ad1ad
                        opacity=0.1,  # transparency
                        layer="below",  # draw below the data
                        line_width=0,
                    )


    if st.session_state.highlight_your_onsets:
        onsets = st.session_state.selected_onsets[['point_x']].values.tolist()
        if len(onsets) > 0:
            for onset in st.session_state.selected_onsets[['point_x']].values.tolist():
                onset = float(math.floor(onset[0]))
                fig.add_shape(
                    # adding a Rectangle for seizure epoch
                    type="rect",
                    x0=onset,  # start time of seizure
                    x1=onset + 2.0,  # end time of seizure (2 seconds after start)
                    y0=-150,  # start y (adjust according to your scale)
                    y1=offset * len(channels),  # end y
                    fillcolor="#7e35ac",  # color of the shaded area, og: #5ad1ad
                    opacity=0.1,  # transparency
                    layer="below",  # draw below the data
                    line_width=0,
                )


    # Create custom y-axis tick labels and positions
    yticks = [i * offset_value for i in range(len(channels))]
    ytick_labels = channels

    # Format the fig
    fig.update_layout(
        # title="",
        xaxis=dict(
            # domain=[0.0, 1.0],
            rangeslider=dict(
                visible=True,
                thickness=0.06,  # adjust thickness (0.1 means 10% of the plot height)
                range=[0.0, df["time"].iloc[-1]],  # range of beginning to end
            ),
            range=[0.0, 20.0],
            tickvals=df[df["time"] % 1.0 == 0.0]["time"].values,
            ticktext=tick_text,
            showgrid=True,
            gridcolor="#bdbdbd",
            zeroline=False,
        ),
        yaxis={
            "tickvals": yticks,
            "ticktext": ytick_labels,
            "tickmode": "array",
            "range": [(-1.5), (max(yticks) + offset_value + 0.5)],
            "showgrid": False,
            "zeroline": False,
        },
        legend=dict(
            traceorder="reversed",
        ),
        height=800,
        margin=dict(t=20, l=0, r=0, b=5),
    )

    return fig
