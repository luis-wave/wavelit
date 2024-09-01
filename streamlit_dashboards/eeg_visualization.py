import time

import boto3
import streamlit as st
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from mywaveanalytics.pipelines.abnormality_detection_pipeline import \
    SeizureDxPipeline

from data_models.abnormality_parsers import serialize_aea_to_pandas
from graphs.eeg_viewer import draw_eeg_graph


def eeg_visualization_dashboard():
    # Set page configuration

    # Title
    st.title("EEG Visualization Dashboard")

    if "mw_object" not in st.session_state:
        st.error("Please load EEG data")
    else:
        col1, col2 = st.columns(2)

        if st.session_state.filename and ("/tmp/" not in st.session_state.filename):
            col1.metric("Filename", st.session_state.filename)
        elif st.session_state.eeg_id:
            col1.metric("EEGId", st.session_state.eeg_id)

        col2.metric("Recording Date", st.session_state.recording_date)

        # Check if `mw_object` is available
        if "mw_object" in st.session_state and st.session_state.mw_object:
            mw_object = st.session_state.mw_object
            mw_copy = mw_object.copy()


            # Override selected reference if necessary. For hyperlinks
            query_params = st.query_params.to_dict()
            if "ref" in query_params:
                selected_reference = query_params["ref"]
            else:
                # Reference selection
                ref = st.selectbox(
                    "Choose EEG Reference",
                    options=[
                        "linked ears",
                        "centroid",
                        "bipolar longitudinal",
                    ],
                    index=0,  # Default to 'linked ears'
                )

                selected_references = {
                    "linked ears": "linked_ears",
                    "bipolar longitudinal": "bipolar_longitudinal",
                    "centroid": "centroid",
                }

                selected_reference = selected_references[ref]

            # Offset value slider
            offset_value = st.slider(
                "Vertical Offset Between Channels",
                min_value=5,
                max_value=700,
                value=100,
                step=5,
            )

            if st.button("AEA Detection"):
                with st.spinner("Running..."):
                    mw_object = st.session_state.mw_object
                    pipeline = SeizureDxPipeline(
                        mw_object.copy(), reference=selected_reference
                    )
                    pipeline.run()
                    analysis_json = pipeline.analysis_json

                    aea_df = serialize_aea_to_pandas(
                        analysis_json, ref=selected_reference
                    )
                    st.session_state["aea"][selected_reference] = aea_df

            # Create DataFrame from MyWaveAnalytics object
            df = st.session_state.eeg_graph[selected_reference]
            if df is not None:
                # Generate the Plotly figure
                with st.spinner("Rendering..."):
                    fig = draw_eeg_graph(df, offset_value, selected_reference)

                    # Display the Plotly figure
                    st.plotly_chart(fig, use_container_width=True)

            # Retrieve ahr from session state
            aea = st.session_state.get("aea", None)

            if aea is not None:
                if not aea[selected_reference].empty:
                    st.header("Edit AEA Predictions")
                    with st.form("data_editor_form", border=False):
                        editable_df = st.session_state.aea[selected_reference].copy()
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
                            st.session_state["data"] = edited_df
                            st.success("Changes saved successfully!")

                            try:
                                # Convert DataFrame to CSV and save it locally
                                csv_file_name = f"{st.session_state.eeg_id}"
                                edited_df.to_csv(csv_file_name, index=False)

                                # S3 client setup
                                s3 = boto3.client("s3")
                                bucket_name = "lake-superior-prod"
                                file_path = f"eeg-lab/abnormality_bucket/streamlit_validations/aea/{csv_file_name}_{selected_reference}.csv"

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

        else:
            st.error(
                "No EEG data available. Please upload an EEG file on the main page."
            )


# To run the function as a Streamlit app
if __name__ == "__main__":
    eeg_visualization_dashboard()
