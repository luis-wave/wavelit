import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from mywaveanalytics.libraries import references
from mywaveanalytics.pipelines.abnormality_detection_pipeline import \
    SeizureDxPipeline

from data_models.abnormality_parsers import serialize_aea_to_pandas
from graphs.eeg_viewer import draw_eeg_graph

# Streamlit app setup
st.set_page_config(page_title="EEG Visualization", layout="wide")
# Title
st.title("EEG Visualization Dashboard")

if 'mw_object' not in st.session_state:
    st.error("Please load EEG data")
else:


    col1, col2 = st.columns(2)

    if st.session_state.filename and ('/tmp/' not in st.session_state.filename) :
        #st.header(st.session_state.filename)
        col1.metric("Filename", st.session_state.filename)
    elif st.session_state.eeg_id:
        col1.metric("EEGId", st.session_state.eeg_id)

    col2.metric("Recording Date", st.session_state.recording_date )

    # Check if `mw_object` is available
    if 'mw_object' in st.session_state and st.session_state.mw_object:
        mw_object = st.session_state.mw_object
        mw_copy = mw_object.copy()

        # Reference selection
        ref = st.selectbox(
            "Choose EEG Reference",
            options=[
                "linked ears",
                "centroid",
                "bipolar longitudinal",
            ],
            index=0  # Default to 'linked ears'
        )

        selected_references = {
            "linked ears": "linked_ears",
            "bipolar longitudinal": "bipolar_longitudinal",
            "centroid": "centroid"
        }

    for i, channel in enumerate(channels):
        offset = i * offset_value
        fig.add_trace(
            go.Scattergl(
                x=df['time'],
                y=df[channel] + offset,  # Apply vertical offset
                mode="lines",
                name=channel,
                line=dict(color="#4E4E4E"),
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
                x0=onset,  # start time of seizure
                x1=onset + 2,  # end time of seizure (2 seconds after start)
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
        title=filename,
        xaxis_title="Time",
        yaxis_title="EEG Channels",
        xaxis={"rangeslider": {"visible": True}, 'range': [0, 20]},
        yaxis={
            "tickvals": yticks,
            "ticktext": ytick_labels,
            "tickmode": "array",
            "range": [-100, max(yticks) + offset_value]
        },
        height=1000,  # Consistent height
    )
    return fig

# Function to assign ECG channel types if present
def assign_ecg_channel_type(raw, ecg_channels):
    existing_channels = raw.ch_names
    channel_types = {ch: 'ecg' for ch in ecg_channels if ch in existing_channels}
    raw.set_channel_types(channel_types)


        selected_reference = selected_references[ref]


        # Offset value slider
        offset_value = st.slider(
            "Vertical Offset Between Channels",
            min_value=5, max_value=700, value=100, step=5
        )

        if st.button("AEA Detection"):
            with st.spinner("Running..."):
                mw_object = st.session_state.mw_object
                pipeline = SeizureDxPipeline(mw_object.copy(), reference=selected_reference)
                pipeline.run()
                analysis_json = pipeline.analysis_json

                aea_df = serialize_aea_to_pandas(analysis_json, ref=selected_reference)
                st.session_state['aea'][selected_reference] = aea_df

        # Create DataFrame from MyWaveAnalytics object
        df = st.session_state.eeg_graph[selected_reference]
        if df is not None:
            # Generate the Plotly figure
            with st.spinner("Rendering..."):
                fig = draw_eeg_graph(df, offset_value, selected_reference)

                # Display the Plotly figure
                st.plotly_chart(fig, use_container_width=True)

        # Retrieve ahr from session state
        aea = st.session_state.get('aea', None)

        if aea is not None:
            if not aea[selected_reference].empty:
                st.header("Edit AEA Predictions")
                with st.form("data_editor_form", border=False):
                    editable_df = st.session_state.aea[selected_reference].copy()
                    edited_df = st.data_editor(
                        editable_df,
                        column_config={
                            "probability": st.column_config.ProgressColumn(
                                "Probability",
                                help="The probability of a seizure occurrence (shown as a percentage)",
                                min_value=0,
                                max_value=1,  # Assuming the probability is normalized between 0 and 1
                            ),
                        },
                        hide_index=True,
                )
                    # Submit button for the form
                    submitted = st.form_submit_button("Save Changes")

                    if submitted:
                        # Update the session state with the edited DataFrame
                        st.session_state['data'] = edited_df
                        st.success("Changes saved successfully!")

                        # Display the potentially updated DataFrame
                        st.write("Updated Data:", st.session_state.aea[selected_reference])

    else:
        st.error("No EEG data available. Please upload an EEG file on the main page.")


