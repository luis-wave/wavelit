# wavelets.py

import numpy as np
import pywt
import plotly.graph_objects as go
import mne
import streamlit as st
from pipeline import bipolar_transverse_montage
import matplotlib.pyplot as plt

st.set_page_config(page_title="Wavelet Analysis Dashboard", layout="wide")
st.title("Continous Wavelet Transform (CWT) Spectrogram")

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

    def calculate_and_plot_cwt_spectrogram(mw_object, channels=["P3-Pz", "Pz-P4", "P4-T6", "T5-O1", "O1-O2", "O2-T6"]):
        """
        Calculate and plot the CWT spectrogram for the average of the specified posterior channels.
        """
        # Extract the data for the specified channels
        raw = mw_object.eeg
        raw.resample(50)
        raw = bipolar_transverse_montage(raw)
        picks = mne.pick_channels(raw.info['ch_names'], include=channels)
        data, times = raw[picks, :]

        # Calculate the average signal
        average_signal = np.mean(data, axis=0)

        # Manually set the scales to explore 8-13 Hz
        frequencies = np.linspace(8, 13, num=20)
        scales = pywt.scale2frequency('morl', 1) / frequencies * raw.info['sfreq']

        # Calculate the CWT spectrogram for the average signal
        spectrogram, freqs = pywt.cwt(average_signal, scales, 'morl', sampling_period=1/raw.info['sfreq'])
        power = np.abs(spectrogram) ** 2

        # Replace power values over a certain threshold with 0
        threshold = 1.2e-9
        power[power > threshold] = 0

        # Create the plot
        fig = go.Figure()
        fig.add_trace(go.Surface(z=power, x=times, y=freqs, colorscale='Viridis'))

        # Update layout for 3D plotting
        fig.update_layout(
            title="CWT Spectrogram of Average Posterior Channels",
            scene=dict(
                xaxis_title='Time (s)',
                yaxis_title='Frequency (Hz)',
                zaxis_title='Power (µV²)'
            ),
            width=1200,
            height=900
        )

        return fig

    def calculate_and_plot_cwt_spectrogram2(mw_object, channels=["P3-Pz", "Pz-P4", "P4-T6", "T5-O1", "O1-O2", "O2-T6"]):
        """
        Calculate and plot the CWT spectrogram for the average of the specified posterior channels.
        """
        # Extract the data for the specified channels
        raw = mw_object.eeg
        raw.resample(50)
        raw = bipolar_transverse_montage(raw)
        picks = mne.pick_channels(raw.info['ch_names'], include=channels)
        data, times = raw[picks, :]

        # Calculate the average signal
        average_signal = np.mean(data, axis=0)

        # Manually set the scales to explore 8-13 Hz
        frequencies = np.linspace(8, 13, num=20)
        scales = pywt.scale2frequency('morl', 1) / frequencies * raw.info['sfreq']

        # Calculate the CWT spectrogram for the average signal
        spectrogram, freqs = pywt.cwt(average_signal, scales, 'morl', sampling_period=1/raw.info['sfreq'])
        power = np.abs(spectrogram) ** 2

        # Replace power values over a certain threshold with 0
        threshold = 1.2e-9
        power[power > threshold] = 0

        # Create the plot
        fig = go.Figure(data=go.Heatmap(
            z=power,
            x=times,
            y=freqs,
            colorscale='Viridis'
        ))

        # Update layout for 2D plotting
        fig.update_layout(
            title=st.session_state.recording_date,
            xaxis_title='Time (s)',
            yaxis_title='Frequency (Hz)',
            width=1200,
            height=900
        )

        return fig

    # Check if `mw_object` is available
    if 'mw_object' in st.session_state and st.session_state.mw_object:
        mw_object = st.session_state.mw_object
        mw_object = mw_object.copy()

        # Generate and display CWT spectrogram plot
        fig = calculate_and_plot_cwt_spectrogram(mw_object)
        st.plotly_chart(fig)

    else:
        st.error("No EEG data available. Please upload an EEG file on the main page.")
