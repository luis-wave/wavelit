import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from mywaveanalytics.pipelines.abnormality_detection_pipeline import \
    ArrhythmiaDxPipeline

from utils.helpers import format_single


def filter_predictions(predictions, confidence_threshold=0.9, epoch_length=0.7):
    # Extract the probabilities array from the dictionary
    probabilities = predictions['predictions']
    r_peaks = predictions['r_peaks']

    # Initialize lists to store the data
    onsets = []
    confidences = []
    is_seizure = []

    # Iterate through the probabilities to find values above the threshold
    for index, probability in enumerate(probabilities):
        if probability > confidence_threshold:
            onsets.append(r_peaks[index])
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
        'is_arrythmia': is_seizure
    })

    df['ahr_times'] = df['onsets'].apply(format_single)

    return df


# Function to convert a MyWaveAnalytics object to a DataFrame with resampling
def mw_to_dataframe_resampled(mw_object, sample_rate=50):
    try:
        raw = mw_object.eeg
        raw.pick_channels(['ECG'])
        raw = raw.resample(sample_rate)
        df = raw.to_data_frame()
        df['time'] = df.index / sample_rate
        return df
    except Exception as e:
        st.error(f"Failed to convert EEG data to DataFrame: {e}")
        return None



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



# Streamlit app setup
st.set_page_config(page_title="ECG Visualization", layout="wide")
# Title
st.title("ECG Visualization Dashboard")
st.session_state["data"] = None

# st.json(st.session_state.ahr)

if 'mw_object' not in st.session_state:
    st.error("Please load EEG data")

else:

    if st.session_state.heart_rate == None:
        st.error("No ECG data available. Please upload an EEG file with ECG data on the main page.")
    else:



        heart_rate_bpm = round(st.session_state.heart_rate,1)
        heart_rate_std_dev = round(st.session_state.heart_rate_std_dev,1)


        col1, col2, col3 = st.columns(3)

        if st.session_state.filename and ('/tmp/' not in st.session_state.filename) :
            #st.header(st.session_state.filename)
            col1.metric("Filename", st.session_state.filename)
        elif st.session_state.eeg_id:
            col1.metric("EEGId", st.session_state.eeg_id)

        col2.metric("Recording Date", st.session_state.recording_date)

        if st.session_state.ahr:
            col3.metric("Abnormal ECG Events", len(st.session_state.ahr['onsets']))
        else:
            col3.metric("Abnormal ECG Events", "N/A")

        st.header(f"Heart Rate (bpm): {heart_rate_bpm} ± {heart_rate_std_dev}")

        # Check if `mw_object` is available
        if ('mw_object' in st.session_state) and ('heart_rate' in st.session_state) and st.session_state.mw_object:
            mw_object = st.session_state.mw_object
            mw_copy = mw_object.copy()

            # Offset value slider
            offset_value = st.slider(
                "Vertical Offset Between Channels",
                min_value=0, max_value=5000, value=2000, step=5
            )

            if st.button("AHR Detection"):
                with st.spinner("Running..."):
                    mw_object = st.session_state.mw_object

                    pipeline = ArrhythmiaDxPipeline(mw_object.copy())
                    pipeline.run()
                    analysis_json = pipeline.analysis_json

                    ahr_df = filter_predictions(analysis_json)
                    st.session_state['data'] = ahr_df

            # Create DataFrame from MyWaveAnalytics object
            df = st.session_state.ecg_graph

            # Generate the Plotly figure
            with st.spinner("Rendering..."):
                fig = create_plotly_figure(df, offset_value)

                # Display the Plotly figure
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.error("No ECG data available. Please upload an EEG file on the main page.")


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
                        st.session_state.data,
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