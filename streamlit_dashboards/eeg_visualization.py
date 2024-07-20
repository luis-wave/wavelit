import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from mywaveanalytics.libraries import references
from mywaveanalytics.pipelines.abnormality_detection_pipeline import \
    SeizureDxPipeline

from data_models.abnormality_parsers import serialize_aea_to_pandas
from graphs.eeg_viewer import draw_eeg_graph


def eeg_visualization_dashboard():
    # Set page configuration
    #st.set_page_config(page_title="EEG Visualization", layout="wide")

    # Title
    st.title("EEG Visualization Dashboard")

    if 'mw_object' not in st.session_state:
        st.error("Please load EEG data")
    else:
        col1, col2 = st.columns(2)

        if st.session_state.filename and ('/tmp/' not in st.session_state.filename):
            col1.metric("Filename", st.session_state.filename)
        elif st.session_state.eeg_id:
            col1.metric("EEGId", st.session_state.eeg_id)

        col2.metric("Recording Date", st.session_state.recording_date)

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


# To run the function as a Streamlit app
if __name__ == "__main__":
    eeg_visualization_dashboard()
