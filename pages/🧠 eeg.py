import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from mywaveanalytics.libraries import references
from mywaveanalytics.pipelines.abnormality_detection_pipeline import \
    SeizureDxPipeline

from utils.helpers import (assign_ecg_channel_type, filter_eeg_ecg_channels,
                           format_single, order_channels)

# Streamlit app setup
st.set_page_config(page_title="EEG Visualization", layout="wide")
st.session_state["data"] = None
# Title
st.title("EEG Visualization Dashboard")
st.json(st.session_state.aea)

#st.json(st.session_state.autoreject)

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

    #col3.metric("Abnormal EEG Events", len(st.session_state.aea['onsets']))

    def filter_predictions(predictions, confidence_threshold=0.75, epoch_length=2, ref = "N/A"):
        # Extract the probabilities array from the dictionary
        probabilities = predictions['predictions']

        # Initialize lists to store the data
        onsets = []
        confidences = []
        is_seizure = []

        # Iterate through the probabilities to find values above the threshold
        for index, probability in enumerate(probabilities):
            if probability > confidence_threshold:
                onsets.append(index * epoch_length)
                confidences.append(probability)
                is_seizure.append(True)

            else:
                # Append data for all lists even if they do not meet the threshold
                onsets.append(index * epoch_length)
                confidences.append(probability)
                is_seizure.append(False)

        # Create a DataFrame with the collected data
        df = pd.DataFrame({
            'onsets': onsets,
            'probability': confidences,
            'is_seizure': is_seizure
        })
        df['montage'] = ref

        df['aea_times'] = df['onsets'].apply(format_single)

        return df


    # Plotly figure creation
    def create_plotly_figure(df, offset_value):
        fig = go.Figure()

        channels = df.columns.drop('time')

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

    # Check if `mw_object` is available
    if 'mw_object' in st.session_state and st.session_state.mw_object:
        # mw_object = st.session_state.mw_object
        # mw_copy = mw_object.copy()

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


        # Offset value slider
        offset_value = st.slider(
            "Vertical Offset Between Channels",
            min_value=5, max_value=700, value=100, step=5
        )

        if st.button("AEA Detection"):
            with st.spinner("Running..."):
                mw_object = st.session_state.mw_object

                if ref == "linked ears":
                    selected_reference = "linked_ears"
                elif ref == 'bipolar longitudinal':
                    selected_reference = 'bipolar_longitudinal'
                elif ref == "centroid":
                    selected_reference = "centroid"
                else:
                    selected_reference = "linked_ears"

                pipeline = SeizureDxPipeline(mw_object.copy(), reference=selected_reference)
                pipeline.run()
                analysis_json = pipeline.analysis_json

                aea_df = filter_predictions(analysis_json, ref=selected_reference)
                st.session_state['data'] = aea_df

        if ref == "linked ears":
            selected_reference = "linked_ears"
        elif ref == 'bipolar longitudinal':
            selected_reference = 'bipolar_longitudinal'
        elif ref == "centroid":
            selected_reference = "centroid"
        else:
            selected_reference = "linked_ears"

        # Create DataFrame from MyWaveAnalytics object
        df = st.session_state.eeg_graph[selected_reference]
        if df is not None:
            # # Filter the DataFrame to include only selected channels
            # missing_channels = [channel for channel in selected_channels if channel not in df.columns]
            # if missing_channels:
            #     st.warning(f"Missing channels in the file: {missing_channels}")
            #     selected_channels = [channel for channel in selected_channels if channel in df.columns]
            # Generate the Plotly figure
            with st.spinner("Rendering..."):
                fig = create_plotly_figure(df, offset_value)

                # Display the Plotly figure
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("No EEG data available. Please upload an EEG file on the main page.")


    # Initialize the DataFrame in the session state if it hasn't been initialized yet
    if 'data' not in st.session_state or st.session_state['data'] is None:
        st.session_state['data'] = pd.DataFrame()

        # Use a form to contain the data editor and submit button
    if not st.session_state.data.empty:
        if not st.session_state.data.empty:
            st.header("Edit AEA Predictions")
            with st.form("data_editor_form", border=False):
                editable_df = st.session_state.data.copy()
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
                    st.write("Updated Data:", st.session_state['data'])