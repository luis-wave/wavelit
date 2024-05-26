# wavelets.py

import numpy as np
import pywt
import plotly.graph_objects as go
import mne
import streamlit as st
from pipeline import bipolar_transverse_montage

st.set_page_config(page_title="CWT Spectrogram", layout="wide")

st.title("CWT Spectrogram")

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
    frequencies = np.linspace(8, 13, num=10)
    scales = pywt.scale2frequency('morl', 1) / frequencies * raw.info['sfreq']

    # Calculate the CWT spectrogram for the average signal
    spectrogram, freqs = pywt.cwt(average_signal, scales, 'morl', sampling_period=1/raw.info['sfreq'])
    power = np.abs(spectrogram) ** 2

    # Clip the power values
    power = np.clip(power, None, 7e-9)

    # Create the plot
    fig = go.Figure()
    fig.add_trace(go.Surface(z=power, x=times, y=freqs, colorscale='thermal'))

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

# Check if `mw_object` is available
if 'mw_object' in st.session_state and st.session_state.mw_object:
    mw_object = st.session_state.mw_object
    mw_object = mw_object.copy()

    # Generate and display CWT spectrogram plot
    st.subheader("CWT Spectrogram")
    fig = calculate_and_plot_cwt_spectrogram(mw_object)
    st.plotly_chart(fig)

else:
    st.error("No EEG data available. Please upload an EEG file on the main page.")
