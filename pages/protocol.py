import numpy as np
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import joblib
from pathlib import Path
from scipy.stats import kurtosis
from scipy.signal import welch, find_peaks
from mywaveanalytics.utils.params import NGBOOST_MODEL_FILEPATH, DEFAULT_RESAMPLING_FREQUENCY
from mywaveanalytics.utils.helpers import iqr_threshold

import mne

# Load the NGBoost model
ngb_regressor = joblib.load(NGBOOST_MODEL_FILEPATH)

def plot_psd_against_freqs(file, psd_avg, freqs, protocol, std_dev):
    psd = np.array(psd_avg)
    psd = (psd * 10**12) ** 0.5
    data = pd.DataFrame({"Frequency": freqs, "Posterior Magnitude Spectra": psd})
    filtered_data = data[(data["Frequency"] >= 3) & (data["Frequency"] <= 20)]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=filtered_data["Frequency"],
            y=filtered_data["Posterior Magnitude Spectra"],
            mode="lines",
            name="Posterior Magnitude Spectra",
        )
    )
    fig.add_vline(
        x=protocol,
        line=dict(color="red", dash="dash"),
        annotation_text=f"Protocol: {round(protocol, 1)} Hz",
        annotation_position="top left",
    )
    fig.add_vrect(
        x0=protocol - std_dev,
        x1=protocol + std_dev,
        fillcolor="red",
        opacity=0.3,
        line_width=0,
        annotation_text=f"Confidence Interval: ±{round(std_dev, 2)} Hz",
        annotation_position="bottom left",
    )
    fig.update_layout(
        title=f"{file}",
        xaxis_title="Frequency (Hz)",
        yaxis_title="Magnitude Spectra (µV)",
        yaxis=dict(range=[0, max(filtered_data["Posterior Magnitude Spectra"]) * 1.1]),
        legend_title="Legend",
        template="plotly_white",
    )
    st.plotly_chart(fig)

def compute_ngboost_protocol(mw_object):
    try:
        mw_copy = mw_object.copy()
        # Compute alpha peak feature stats
        peak_stats = compute_alpha_peak_stats(mw_copy)

        # Predict using the loaded NGBoost model
        ngb_protocol = ngb_regressor.predict(peak_stats)[0]
        ngb_std_dev = ngb_regressor.pred_dist(peak_stats).params['scale'][0]

        # Compute Power Spectral Density (PSD) stats
        psd_avg, freqs = mne.time_frequency.psd_welch(mw_copy.eeg, picks=['O1', "O2", "P3", "P4", "Pz"])

        return ngb_protocol, ngb_std_dev, psd_avg.mean(axis=0), freqs
    except Exception as e:
        st.error(f"Protocol generation failed: {e}")
        return None, None, None, None


def slopes_around_maxima(signal):
    """
    Calculate the sum of absolute slopes around the two points preceding and
    proceeding from local maxima.

    Parameters:
        signal (array-like): The input signal.

    Returns:
        list: List of tuples with (local maxima, sum of absolute slopes).
    """
    # Detect local maxima
    peaks = []
    for i in range(1, len(signal) - 3):
        if signal[i - 1] < signal[i] > signal[i + 1]:
            peaks.append(i)

    # Calculate the absolute slopes
    slopes = []
    for peak in peaks:
        total_slope = 0
        if peak - 2 >= 0 and peak + 2 < len(signal):  # Ensure we don't go out of bounds
            total_slope += abs(signal[peak] - signal[peak - 1])  # First point preceding
            total_slope += abs(
                signal[peak] - signal[peak - 2]
            )  # Second point preceding
            total_slope += abs(
                signal[peak] - signal[peak + 1]
            )  # First point proceeding
            total_slope += abs(
                signal[peak] - signal[peak + 2]
            )  # Second point proceeding

        slopes.append(total_slope)

    return np.array(slopes)

def make_epochs(mw_object, time_window=20):
    """
    Break MyWaveObject into epochs based on specified time window length.

    Parameters:
        mw_object

    Returns:
        Epochs: Mne's epoch class.
    """
    raw = mw_object.eeg

    epochs = mne.make_fixed_length_epochs(
        raw, duration=time_window, preload=True, overlap=0
    )

    return epochs

def filter_psd(psd, fs=DEFAULT_RESAMPLING_FREQUENCY):
    """
    Apply a filtering process to the power spectral density (PSD) data.

    Parameters:
    psd: The PSD data to be filtered.
    fs: Sampling frequency.

    Returns:
    tuple: A tuple containing the frequencies and filtered PSD values.
    """
    f, psd_values = welch(psd, fs=fs)
    threshold = iqr_threshold(psd_values.sum(axis=1))
    valid_indices = np.where(psd_values.sum(axis=1) <= threshold)[0]
    return f, psd_values[valid_indices]

def calculate_alpha_peaks(psd, frequencies):
    """
    Calculate alpha peaks and their corresponding slopes from the PSD data.

    Parameters:
    psd: The power spectral density data.
    frequencies: Array of frequency values corresponding to the PSD data.

    Returns:
    tuple: Arrays of alpha peak frequencies and their respective slopes.
    """
    alpha_peaks, alpha_slopes = [], []
    for spectrum in psd:
        peaks, _ = find_peaks(spectrum)
        slopes = slopes_around_maxima(spectrum)
        alpha_range = np.where((frequencies >= 8) & (frequencies < 13))[0]
        alpha_peaks_indices = np.intersect1d(peaks, alpha_range)
        alpha_peaks.extend(frequencies[alpha_peaks_indices])
        alpha_slopes.extend(slopes[np.where(np.isin(peaks, alpha_peaks_indices))[0]])
    return np.array(alpha_peaks), np.array(alpha_slopes)

def filter_by_slope(peaks, slopes, threshold_percentile=67):
    """
    Filter alpha peaks based on their slopes, using a percentile threshold.

    Parameters:
    peaks: Array of alpha peak frequencies.
    slopes: Array of slopes corresponding to the alpha peaks.
    threshold_percentile: Percentile value used to determine the slope threshold.

    Returns:
    tuple: Filtered arrays of alpha peaks and slopes.
    """
    threshold = np.percentile(slopes, threshold_percentile)
    valid_indices = np.where(slopes >= threshold)
    return peaks[valid_indices], slopes[valid_indices]

def compute_peak_statistics(peaks, slopes, columns):
    """
    Compute statistical measures for each unique peak in the provided columns.

    Parameters:
    peaks: Array of alpha peak frequencies.
    slopes: Array of slopes corresponding to the alpha peaks.
    columns: List of predefined frequency columns for the analysis.

    Returns:
    tuple: (DataFrame of statistics, Dictionary of statistics)
    """
    peak_dict = {peak: [] for peak in columns}
    for peak, slope in zip(peaks, slopes):
        if peak in peak_dict:
            peak_dict[peak].append(slope)

    stats_dict = {}
    for peak, vals in peak_dict.items():
        if not vals:
            stats = [0, 0, 0, 0]  # If all peaks are removed within a certain frequency bin, set all stats to 0
        else:
            stats = [
                len(vals),
                np.median(vals),
                np.percentile(vals, 99) - np.percentile(vals, 1),
                kurtosis(vals)
            ]

        stats_dict[peak] = {
            'count': stats[0],
            'median': stats[1],
            'std_dev': stats[2],
            'kurtosis': stats[3]
        }

    df = pd.DataFrame(stats_dict, index=["count", "median", "std_dev", "kurtosis"])

    return df

def compute_alpha_peak_stats(mw_object, time_window=2.56):
    """
    Main function to compute alpha peak statistics from EEG data.

    Parameters:
    mw_object: Data object containing EEG measurements.
    time_window: Time window for epoch creation.

    Returns:
    Numpy array: flattened array of alpha peak statistics
    """
    epochs = make_epochs(mw_object, time_window)
    posterior_average_raw_data = epochs.get_data(units="uV", picks=["Pz", "P3", "P4", "O1", "O2"]).mean(axis=1)
    frequencies, psd = filter_psd(posterior_average_raw_data)
    alpha_peaks, alpha_slopes = calculate_alpha_peaks(psd, frequencies)
    filtered_peaks, filtered_slopes = filter_by_slope(alpha_peaks, alpha_slopes)
    columns = frequencies[(frequencies > 8) & (frequencies < 13)]

    df = compute_peak_statistics(filtered_peaks, filtered_slopes, columns)
    df_normalized = df.div(df.sum(axis=1), axis=0)

    # Convert dictionary to features array
    features = np.array([[float(k), v['count'], v['median'], v['std_dev'], v['kurtosis']] for k, v in df_normalized.to_dict().items()])

    # Extract the first three features for peak_stats
    peak_stats = np.array([i[:3] for i in features]).flatten().reshape(1, -1)

    return peak_stats

st.title("NGBoost Protocol Recommendations")

if 'mw_object' in st.session_state and st.session_state.mw_object:
    mw_object = st.session_state.mw_object
    protocol, std_dev, psd_avg, freqs = compute_ngboost_protocol(mw_object)
    if protocol is not None:
        st.write(f"Protocol: {protocol:.2f} Hz ± {std_dev:.2f} Hz")
        plot_psd_against_freqs(st.session_state.fname, psd_avg, freqs, protocol, std_dev)
    else:
        st.error("Unable to generate protocol for the uploaded file.")
else:
    st.error("No EEG data available. Please upload an EEG file on the main page.")
