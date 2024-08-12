import time

import boto3
import streamlit as st
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from mywaveanalytics.pipelines.abnormality_detection_pipeline import \
    ArrhythmiaDxPipeline

from data_models.abnormality_parsers import serialize_ahr_to_pandas
from graphs.ecg_viewer import draw_ecg_figure


def ecg_visualization_dashboard():
    # Set page configuration
    #st.set_page_config(page_title="ECG Visualization", layout="wide")

    # Title
    st.title("ECG Visualization Dashboard")
    st.session_state["data"] = None

    if 'mw_object' not in st.session_state:
        st.error("Please load EEG data")
    else:
        if st.session_state.heart_rate is None:
            st.error("No ECG data available. Please upload an EEG file with ECG data on the main page.")
        else:
            heart_rate_bpm = round(st.session_state.heart_rate, 1)
            heart_rate_std_dev = round(st.session_state.heart_rate_std_dev, 1)

            col1, col2 = st.columns(2)

            if st.session_state.filename and ('/tmp/' not in st.session_state.filename):
                col1.metric("Filename", st.session_state.filename)
            elif st.session_state.eeg_id:
                col1.metric("EEGId", st.session_state.eeg_id)

            col2.metric("Recording Date", st.session_state.recording_date)

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

                        ahr_df = serialize_ahr_to_pandas(analysis_json)
                        st.session_state['ahr'] = ahr_df

                # Create DataFrame from MyWaveAnalytics object
                df = st.session_state.ecg_graph

                # Generate the Plotly figure
                with st.spinner("Rendering..."):
                    fig = draw_ecg_figure(df, offset_value)

                    # Display the Plotly figure
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No ECG data available. Please upload an EEG file on the main page.")

            # Retrieve ahr from session state
            ahr = st.session_state.get('ahr', None)

            if ahr is not None and not ahr.empty:
                st.header("Edit AHR Predictions")
                with st.form("ecg_data_editor_form", border=False):
                    editable_df = ahr.copy()
                    editable_df["reviewer"] = st.session_state["user"]
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
                        st.session_state['ahr'] = edited_df
                        st.success("Changes saved successfully!")

                        try:
                            # Convert DataFrame to CSV and save it locally
                            csv_file_name = f'{st.session_state.eeg_id}.csv'
                            edited_df.to_csv(csv_file_name, index=False)

                            # S3 client setup
                            s3 = boto3.client("s3")
                            bucket_name = 'lake-superior-prod'
                            file_path = f'eeg-lab/abnormality_bucket/streamlit_validations/ahr/{csv_file_name}'

                            # Adding metadata
                            processed_date = time.time()
                            _ = s3.upload_file(
                                csv_file_name,
                                bucket_name,
                                file_path,
                                ExtraArgs={
                                    "Metadata": {
                                        "processed_date": str(processed_date),
                                        "file_name": csv_file_name,
                                    }
                                },
                            )
                            print("File uploaded successfully")
                        except NoCredentialsError:
                            st.error("Error: Unable to locate credentials")
                        except PartialCredentialsError:
                            st.error("Error: Incomplete credentials provided")
                        except Exception as e:
                            st.error(f"Error: {e}")

# To run the function as a Streamlit app
if __name__ == "__main__":
    ecg_visualization_dashboard()
