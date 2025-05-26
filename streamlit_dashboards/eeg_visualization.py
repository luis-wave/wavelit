import pandas as pd
import time
from datetime import datetime

import boto3
import streamlit as st
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from mywaveanalytics.pipelines.abnormality_detection_pipeline import SeizureDxPipeline

from mywaveanalytics.utils.params import (
    CHANNEL_ORDER_BIPOLAR_LONGITUDINAL,
    CHANNEL_ORDER_TEMPORAL_CENTRAL_PARASAGITTAL,
    CHANNEL_ORDER_PERSYST,
)

import dsp.graph_preprocessing as waev
import graph_helpers.eeg_viewer_helper as evh
from data_models.abnormality_parsers import serialize_aea_to_pandas
from graphs.eeg_viewer import draw_eeg_graph

import os

DATABRICKS_BUCKET = os.getenv("DATABRICKS_BUCKET")
ABNORMALITY_FEEDBACK_BUCKET = os.getenv("ABNORMALITY_FEEDBACK_BUCKET")


def eeg_visualization_dashboard():
    # Title
    st.title("EEG Visualization Dashboard")

    if "mw_object" not in st.session_state:
        st.error("Please load EEG data")
    else:
        with st.container():
            col1, col2 = st.columns(2)

            if st.session_state.filename and ("/tmp/" not in st.session_state.filename):
                col1.metric("Filename", st.session_state.filename)
            elif st.session_state.eeg_id:
                col1.metric("EEGId", st.session_state.eeg_id)

            col2.metric("Recording Date", st.session_state.recording_date)

        # Check if `mw_object` is available
        if "mw_object" in st.session_state and st.session_state.mw_object:
            mw_object = st.session_state.mw_object
            columns = [
                "x",
                "point_x",
                "timestamp",
                "probability",
                "curve_number",
                "reference",
                "comments",
                "user",
            ]

            if "selected_onsets" not in st.session_state:
                st.session_state.selected_onsets = pd.DataFrame(columns=columns)
            if "current_montage" not in st.session_state:
                st.session_state.current_montage = "linked ears"
            if "ref_index" not in st.session_state:
                st.session_state.ref_index = 0
            if "ref_changed" not in st.session_state:
                st.session_state.ref_changed = None

            with st.container():

                col1, col2 = st.columns(2)

                # Override selected reference if necessary. For hyperlinks
                query_params = st.query_params.to_dict()
                if "ref" in query_params:
                    ref_param = query_params["ref"]
                else:
                    ref_param = None
                with col1:
                    sub_col1, sub_col2, sub_col3, sub_col4 = st.columns(4)
                    with sub_col1:

                        default_ref_index= 0

                        if ref_param == 'le':
                            st.session_state.ref_index = 0
                        if ref_param == 'cz':
                            st.session_state.ref_index = 1
                        if ref_param == 'bpt':
                            st.session_state.ref_index = 2

                        # Reference selection
                        ref = st.selectbox(
                            "Montage",
                            options=[
                                "linked ears",
                                "centroid",
                                "bipolar longitudinal",
                            ],
                            index=st.session_state.get("ref_index", 0),  # Default to linked ears
                            key="ref_selectbox",
                        )

                        selected_references = {
                            "linked ears": "linked_ears",
                            "centroid": "centroid",
                            "bipolar longitudinal": "bipolar_longitudinal",
                        }

                        # Map the selected label to the internal reference
                        selected_reference = selected_references.get(ref)

                        # Validate if the selected reference exists in the EEG graph
                        if selected_reference in st.session_state.eeg_graph.keys():
                            # Update session state for current montage and reference
                            st.session_state.current_montage = selected_reference
                            st.session_state.ref_changed = (
                                selected_reference != st.session_state.get("current_montage", None)
                            )
                        else:
                            st.warning(f"'{ref}' reference is unavailable. Falling back to 'linked ears'.")
                            st.session_state.ref_selectbox = "linked ears"
                            st.session_state.current_montage = "linked_ears"
                            st.session_state.ref_changed = True
                            selected_reference = "linked_ears"

                    with sub_col2:
                        SENSITIVITY_OPTIONS = [
                            "1.0",
                            "2.0",
                            "3.0",
                            "5.0",
                            "7.0",
                            "10.0",
                            "15.0",
                            "20.0",
                            "30.0",
                            "50.0",
                            "70.0",
                            "100.0",
                            "150.0",
                            "200.0",
                            "300.0",
                            "500.0",
                            "700.0",
                            "1000.0",
                        ]

                        # Initialize sensitivity in session state
                        if "sensitivity" not in st.session_state:
                            st.session_state.sensitivity = "10.0"  # Default value

                        # Sensitivity slider
                        st.session_state.sensitivity = st.selectbox(
                            "Sensitivity in uV",
                            options=SENSITIVITY_OPTIONS,
                            index=5,  # Persisted value
                        )

                    # Dummy columns to decrease the width of the dropdown widgets used
                    with sub_col3: pass
                    with sub_col4: pass

                with col2:
                    highlight_your_onsets = st.toggle(
                        "Highlight Your Onsets Purple",
                        key="highlight_your_onsets",
                    )
                    highlight_ml_onsets = st.toggle(
                        "Highlight ML Onsets Red",
                        value=True,
                        key="highlight_ml_onsets",
                    )


            # Create DataFrame from MyWaveAnalytics object
            df = st.session_state.eeg_graph[selected_reference]

            if df is not None:
                # Convert the sensitivity value to float
                eeg_sensitivity_value = float(st.session_state.sensitivity)

                # Generate the Plotly figure
                with st.spinner("Scaling..."):
                    df = waev.scale_dataframe(df=df, eeg_sensitivity_uv=eeg_sensitivity_value)
                with st.spinner("Rendering..."):
                    # Define the order of channels based on reference
                    if selected_reference in ["linked_ears", "centroid"]:
                        ordered_channels = CHANNEL_ORDER_PERSYST[:-2][::-1]
                    elif selected_reference in ["bipolar_longitudinal"]:
                        ordered_channels = CHANNEL_ORDER_BIPOLAR_LONGITUDINAL

                    fig = draw_eeg_graph(df, selected_reference, ordered_channels)

                def select_event_callback():
                    # Turn the event into an ordered list
                    selection_list = evh.event_to_list(
                        st.session_state.plotly_select_event,
                        ordered_channels,
                    )

                    # Add selection list to existing df of selected onsets
                    selected_df = evh.add_list_to_df(
                        st.session_state.get("selected_onsets", pd.DataFrame()),
                        selection_list,
                        sort=True,
                    )
                    # Save to session state the new collection of onsets
                    st.session_state.selected_onsets = selected_df.reset_index(
                        drop=True
                    )

                # Display the Plotly figure
                select_event = st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="plotly_select_event",
                    # on_select="rerun",
                    on_select=select_event_callback,
                    selection_mode="points",
                    config={
                        'scrollZoom': 'x',  # Enable horizontal scrolling with mouse wheel
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                        'doubleClick': 'reset+autosize'
                    }
                )

            with st.container():
                col1, col2 = st.columns(2)

                with col1:
                    tab1, tab2 = st.tabs(["Your Onsets", "ML Onsets"])
                    with tab1:
                        data_editor_table = st.data_editor(
                            st.session_state.get(
                                "selected_onsets", pd.DataFrame(columns=columns)
                            ),
                            key="my_data",
                            num_rows="dynamic",
                            use_container_width=True,
                            height=800,
                            column_config={
                                "x": "Onset",
                                "point_x": "Onset (s)",
                                "timestamp": "Timestamp",
                                "probability": st.column_config.ProgressColumn(
                                    "Probability",
                                    help="The probability of a seizure occurrence (shown as a percentage)",
                                    min_value=0,
                                    max_value=1,  # Assuming the probability is normalized between 0 and 1
                                ),
                                "curve_number": "Channel",
                                "reference": "Montage",
                                "comments": st.column_config.TextColumn(
                                    "Comments",
                                    help="Add a note about this onset",
                                    width="medium",
                                ),
                                "user": "Reviewer",
                            },
                            column_order=(
                                "x",
                                "point_x",
                                "probability",
                                "curve_number",
                                "reference",
                                "comments",
                            ),
                            disabled=(
                                "x",
                                "point_x",
                                "probability",
                                "curve_number",
                                "reference",
                            )
                        )
                        st.session_state.selected_onsets = data_editor_table

                        if st.button("Submit Onsets", type="primary"):
                            try:
                                # Convert DataFrame to CSV and save it locally
                                csv_file_name = f"{st.session_state.eeg_id}"
                                data_editor_table.to_csv(csv_file_name, index=False)

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


                    with tab2:
                        # Retrieve aea from session state
                        aea = st.session_state.get("aea", None)

                        if aea is not None:
                            # Check if the selected reference exists in AEA data
                            if selected_reference in aea and not aea[selected_reference].empty:
                                with st.form("aea_data_editor_form", border=False):
                                    editable_df = st.session_state.aea[
                                        selected_reference
                                    ].copy()
                                    editable_df["reviewer"] = st.session_state["user"]
                                    edited_df = st.data_editor(
                                        editable_df,
                                        use_container_width=True,
                                        height=800,
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
                                            file_path = f"{ABNORMALITY_FEEDBACK_BUCKET}/aea/{csv_file_name}_{selected_reference}.csv"

                                            # Adding metadata
                                            processed_date = time.time()
                                            _ = s3.upload_file(
                                                csv_file_name,
                                                DATABRICKS_BUCKET,
                                                file_path,
                                                ExtraArgs={
                                                    "Metadata": {
                                                        "processed_date": str(
                                                            processed_date
                                                        ),
                                                        "file_name": csv_file_name,
                                                    }
                                                },
                                            )
                                            print("File uploaded successfully")
                                        except NoCredentialsError:
                                            st.error(
                                                "Error: Unable to locate credentials"
                                            )
                                        except PartialCredentialsError:
                                            st.error(
                                                "Error: Incomplete credentials provided"
                                            )
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                            else:
                                # AEA data exists but is empty for this reference
                                if selected_reference in aea:
                                    st.info(f"No ML onsets found for {selected_reference} montage.")
                                else:
                                    st.warning(f"ML onset data not available for {selected_reference} montage.")
                                st.write("**Possible reasons:**")
                                st.write("• No abnormal EEG activity detected.")
                                st.write("• Selected montage not analyzed")
                        else:
                            # No AEA data at all
                            st.warning("ML onset data not loaded.")
                            st.write("**Possible reasons:**")
                            st.write("• EEG data was uploaded manually (ML analysis only available for downloaded EEGs)")
                            
                            # Add a button to try reloading the data
                            if st.button("Try Reloading ML Data", key="reload_ml_data"):
                                current_eeg_id = st.session_state.get("eeg_id")
                                if current_eeg_id:
                                    with st.spinner("Reloading ML onset data..."):
                                        try:
                                            # Re-run the access_eeg_data function to reload ML data
                                            import asyncio
                                            from access_control import access_eeg_data
                                            asyncio.run(access_eeg_data(current_eeg_id))
                                            st.success("ML data reloaded! Please check the ML Onsets tab again.")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Failed to reload ML data: {str(e)}")
                                else:
                                    st.error("No EEG ID available for reloading.")

                with col2:
                    st.subheader(" ")
                    # Text area widget
                    onset_text = st.text_area(
                        label="Onset List",
                        value=", ".join(
                            data_editor_table["x"].astype(str).drop_duplicates()
                        ),
                        label_visibility="collapsed",
                        height=400,
                        key="onset_text_box",
                        disabled=True,
                    )

        else:
            st.error(
                "No EEG data available. Please upload an EEG file on the main page."
            )


# # To run the function as a Streamlit app
if __name__ == "__main__":
    eeg_visualization_dashboard()
