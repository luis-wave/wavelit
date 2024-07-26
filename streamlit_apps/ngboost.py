import base64
import os
import tempfile
import zipfile
import asyncio

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import streamlit as st
from mywaveanalytics.libraries import mywaveanalytics
from mywaveanalytics.pipelines import ngboost_protocol_pipeline



# Function to process each EEG file
def process_eeg_file(file_path, eeg_type):
    try:
        mw_object = mywaveanalytics.MyWaveAnalytics(file_path, None, None, eeg_type)
        pipeline = ngboost_protocol_pipeline.NGBoostProtocolPipeline(mw_object)
        pipeline.run()
        pipeline.analysis_json['file'] = file_path.split("/")[-1]
        return pipeline.analysis_json
    except Exception as e:
        st.error(f"Error processing file {file_path}: {e}")
        return None

# Recursive function to get all files with specific extensions
def get_eeg_files(directory, extensions):
    eeg_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(extensions) and not file.startswith("._"):
                eeg_files.append(os.path.join(root, file))
    return eeg_files

# Function to create a plotly image of the PSD with the protocol line and confidence interval
def create_psd_plot(psd_data, freqs, ngb_protocol, ngb_std_dev):
    psds = np.mean(psd_data, axis=0)
    freqs = np.array(freqs)

    # Find the maximum value in the PSD within the 6-13 Hz range
    mask = (freqs >= 6) & (freqs <= 13)
    max_psd_in_range = max(psds[mask])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=freqs, y=psds, mode='lines', name='PSD'))

    # Add protocol line
    fig.add_trace(go.Scatter(x=[ngb_protocol, ngb_protocol], y=[0, max_psd_in_range], mode='lines',
                             line=dict(color='red', dash='dash'), name='NGB Protocol'))

    # Add confidence interval
    fig.add_trace(go.Scatter(x=[ngb_protocol - ngb_std_dev, ngb_protocol + ngb_std_dev],
                             y=[max_psd_in_range/2, max_psd_in_range/2], mode='lines',
                             line=dict(color='red', width=1), name='Confidence Interval'))

    fig.update_layout(title='PSD with NGB Protocol', xaxis_title='Frequency (Hz)', yaxis_title='PSD',
                      xaxis=dict(range=[4, 20]), yaxis=dict(range=[0, max_psd_in_range]))

    # Convert plotly figure to base64-encoded PNG
    image_base64 = base64.b64encode(fig.to_image(format="png", engine="kaleido")).decode('utf-8')
    return f"data:image/png;base64,{image_base64}"




st.title("NGBoost EEG Analysis App")

# Upload a zipped folder
uploaded_zip = st.file_uploader("Upload a zipped folder containing EEG files", type="zip")

if uploaded_zip:
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Extract the uploaded zip file
            zip_path = os.path.join(tmpdir, "uploaded.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getvalue())
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)

            # Get all EEG files from the extracted content
            eeg_files = get_eeg_files(tmpdir, ('.edf', '.dat', '.401', '.fif', '.vhdr'))
            total_files = len(eeg_files)
            results = []

            if total_files == 0:
                st.error("No valid EEG files found in the uploaded zip file.")

            # Run the NGBoost pipeline on each EEG file
            progress_bar = st.progress(0)
            for i, eeg_file in enumerate(eeg_files):
                if eeg_file.lower().endswith(".edf"):
                    eeg_type = 10
                elif eeg_file.lower().endswith(".dat"):
                    eeg_type = 0
                elif eeg_file.lower().endswith(".401"):
                    eeg_type = 6
                elif eeg_file.lower().endswith(".fif"):
                    eeg_type = 9
                elif eeg_file.lower().endswith(".vhdr"):
                    eeg_type = 11
                else:
                    st.warning(f"Unsupported file type for file: {eeg_file}")
                    continue

                result = process_eeg_file(eeg_file, eeg_type)
                if result is not None:
                    result['psd_plot'] = create_psd_plot(result['psds'], result['freqs'], result['bipolar_ngb_protocol'], result['bipolar_ngb_std_dev'])
                    results.append(result)

                # Update progress bar
                progress_bar.progress((i + 1) / total_files)

            # Display the results in a dataframe
            if results:
                results_df = pd.DataFrame(results)
                st.write("Analysis Complete!")
                st.dataframe(results_df[['file', 'bipolar_ngb_protocol', 'bipolar_ngb_std_dev', 'psd_plot']],
                                column_config={
                                    'psd_plot': st.column_config.ImageColumn("PSD Plot", width='large')
                                }, use_container_width=True)
            else:
                st.error("No results to display. Please check the log for errors.")

        except Exception as e:
            st.error(f"An error occurred while processing the zip file: {e}")
