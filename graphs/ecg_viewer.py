import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# Plotly figure creation
def draw_ecg_figure(df, offset_value):
    fig = go.Figure()

    # Convert time from seconds to 'mm:ss' format
    df['time'] = pd.to_datetime(df['time'], unit='s')
    fig.add_trace(
        go.Scattergl(
            x=df['time'],
            y=df['ECG'],
            mode="lines",
            name='ECG',
            line=dict(color='#4E4E4E'),
        )
    )

    # Retrieve ahr from session state
    ahr = st.session_state.get('ahr', None)

    if ahr is not None and not ahr.empty:
        # Filter epochs where is_arrythmia is True
        abnormal_epochs = ahr[ahr['is_arrhythmia'] == True]['onsets']

        # Add a shape for each abnormal epoch
        for onset in abnormal_epochs:
            fig.add_shape(
                type="rect",
                x0=pd.to_datetime(onset, unit='s'),  # start time of the abnormal epoch
                x1=pd.to_datetime(onset + 0.75, unit='s'),  # end time of the abnormal epoch
                y0=-offset_value,  # start y-coordinate (adjust according to your scale)
                y1=offset_value,  # end y-coordinate
                fillcolor="#FF7373",  # color of the shaded area
                opacity=1,  # transparency
                layer="below",  # draw below the data
                line_width=0,  # no border line
            )

    filename = st.session_state.recording_date

    fig.update_layout(
        title=filename,
        xaxis_title="Time (mm:ss:milliseconds)",
        yaxis_title="Amplitude (µV)",
        xaxis={"rangeslider": {"visible": True}, 'range': [df['time'].iloc[0], df['time'].iloc[0] + pd.Timedelta(seconds=20)], 'tickformat': '%M:%S.%L' },
        yaxis={
            "range": [-1 * offset_value, offset_value]
        },
        height=750,  # Consistent height
    )
    return fig