import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# Plotly figure creation
def create_plotly_figure(df, offset_value):
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

    seizure_epochs = pd.DataFrame()
    # Adding shaded regions for seizure activity
    # Initialize the DataFrame in the session state if it hasn't been initialized yet
    if 'data' not in st.session_state or st.session_state['data'] is None:
        st.session_state['data'] = pd.DataFrame()

        # Use a form to contain the data editor and submit button
    if not st.session_state.data.empty:
        seizure_epochs = st.session_state.data[st.session_state.data['is_arrythmia'] == True]['onsets']




    if seizure_epochs.any().any():
        for onset in seizure_epochs:
            fig.add_shape(
                # adding a Rectangle for seizure epoch
                type="rect",
                x0=pd.to_datetime(onset, unit='s'),  # start time of seizure
                x1=pd.to_datetime(onset + 0.75, unit='s'),  # end time of seizure (2 seconds after start)
                y0=-offset_value,  # start y (adjust according to your scale)
                y1=offset_value,  # end y
                fillcolor="#FF7373",  # color of the shaded area
                opacity=1,  # transparency
                layer="below",  # draw below the data
                line_width=0,
            )


    filename = st.session_state.recording_date


    fig.update_layout(
        title=filename,
        xaxis_title="Time",
        yaxis_title="Electrocardiograph",
        xaxis={"rangeslider": {"visible": True}, 'range': [df['time'].iloc[0], df['time'].iloc[0] + pd.Timedelta(seconds=20)], 'tickformat': '%M:%S.%L' },
        yaxis={
            "range": [-1 * offset_value, offset_value]
        },
        height=750,  # Consistent height
    )
    return fig