import logging

import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib.collections import LineCollection
from matplotlib.ticker import AutoLocator, FuncFormatter, MultipleLocator
from mywaveanalytics.libraries import (eeg_computational_library, filters,
                                       references)
from mywaveanalytics.utils import params
from mywaveanalytics.utils.params import (DEFAULT_RESAMPLING_FREQUENCY,
                                          ELECTRODE_GROUPING)
from scipy.integrate import simps
from scipy.signal import find_peaks, peak_prominences, welch

from graph_utils import preprocessing

import plotly.graph_objs as go
import plotly.express as px

log = logging.getLogger(__name__)


class PersistPipeline:
    def __init__(self, mw_object):
        self.mw_object = mw_object.copy()
        self.ref = None
        self.sampling_rate = mw_object.eeg.info["sfreq"]
        self.epochs = None
        self.freqs = None
        self.psds = None

    def reset(self, mw_object):
        self.mw_object = mw_object.copy()

    def run(self, time_win=10, ref="le"):
        self.ref = ref
        self.epochs = self.preprocess_data(time_win=time_win, ref=ref)
        self.freqs, self.psds = self.calculate_psds()

        # Flatten psds for DataFrame storage
        flattened_psds = self.psds.reshape(
            self.psds.shape[0], -1
        )  # Flattening epochs, channels, and frequency bins

        self.data = pd.DataFrame(
            {"flattened_psds": list(flattened_psds)}  # Store flattened psds
        )

        # Reshape and calculate scores
        self.data["sync_score"] = self.data["flattened_psds"].apply(
            lambda flattened_psd: self.get_total_sync_score(
                self.freqs, np.reshape(flattened_psd, self.psds.shape[1:])
            )
        )

        self.data["alpha"] = self.data["flattened_psds"].apply(
            lambda flattened_psd: get_power(
                freqs=self.freqs, psd=np.reshape(flattened_psd, self.psds.shape[1:])
            )
        )

        self.data["graded_alpha"] = self.data["alpha"].apply(
            lambda x: grade_alpha(x, self.data["alpha"].values)
        )

        self.data["n_bads"] = [
            len(find_leads_off(self.epochs[i])) for i in range(len(self.epochs))
        ]

        # Sort the DataFrame by score in descending order
        self.data = self.data.sort_values(
            by=["n_bads", "graded_alpha", "sync_score"], ascending=[True, True, False]
        )

    def generate_graphs(self):
        for idx in self.data.index[:20]:
            self.combined_plot(epoch_id=idx)

    def preprocess_data(self, time_win=20, ref=None):
        filters.eeg_filter(self.mw_object, 1, 25)
        filters.notch(self.mw_object)
        filters.resample(self.mw_object)
        self.sampling_rate = DEFAULT_RESAMPLING_FREQUENCY

        raw = self.mw_object.eeg

        if ref == "tcp":
            raw = references.temporal_central_parasagittal(self.mw_object)
        if ref == "cz":
            raw = references.centroid(self.mw_object)
        if ref == "blm":
            raw = references.bipolar_longitudinal_montage(self.mw_object)
        if ref == "btm":
            raw = bipolar_transverse_montage(self.mw_object.eeg)

        epochs = mne.make_fixed_length_epochs(
            raw, duration=time_win, preload=True, overlap=time_win - 1
        )
        return epochs

    def calculate_psds(self):
        time_series_eeg = self.epochs.get_data(picks="eeg", units="uV")
        freqs, psds = welch(time_series_eeg, self.sampling_rate)
        return freqs, psds

    def get_total_sync_score(self, eeg_frequencies, power_spectral_density):
        alpha_range = (8, 13)
        frequency_prominence_products = []
        for channel_powers in power_spectral_density:
            alpha_mask = (eeg_frequencies >= alpha_range[0]) & (
                eeg_frequencies <= alpha_range[1]
            )
            alpha_frequencies = eeg_frequencies[alpha_mask]
            alpha_powers = channel_powers[alpha_mask]
            peaks, _ = find_peaks(alpha_powers)
            if not peaks.size:
                continue
            prominences = peak_prominences(alpha_powers, peaks)[0]
            frequency_prominence_products.extend(alpha_frequencies[peaks] * prominences)
        return (
            np.median(frequency_prominence_products)
            if frequency_prominence_products
            else 0
        )

    def combined_plot(
        self,
        epoch_id=1,
    ):
        epochs = self.epochs[epoch_id]
        ref = self.ref

        event_times = self.epochs.events[:, 0] / self.sampling_rate

        # Align channel order to what the lab is used to if applicable
        if ref not in ("tcp", "btm", "blm"):
            new_order = [
                "Fz",
                "Cz",
                "Pz",
                "Fp1",
                "Fp2",
                "F3",
                "F4",
                "F7",
                "F8",
                "C3",
                "C4",
                "T3",
                "T4",
                "P3",
                "P4",
                "T5",
                "T6",
                "O1",
                "O2",
            ]
        if ref == "cz":
            epochs = epochs.drop_channels(["Cz"])
            new_order.remove("Cz")

        # Calculate FFT and plot using Welch's method
        data = epochs.get_data(picks="eeg", units="uV")[0]
        fs = self.sampling_rate
        dmin = data.min()  # smallest value in the array
        dmax = np.percentile(data, 80)  # largest value in the array

        n_rows, n_samples = data.shape

        event_start = event_times[epoch_id]

        rec_date = epochs.info["meas_date"].date().strftime("%d-%b-%Y")

        n_seconds = n_samples / fs

        tmin = epochs.tmin  # start time of each epoch in seconds
        tmax = epochs.tmax  # end time of each epoch in seconds
        t = np.linspace(event_start, event_start + n_seconds, n_samples)

        # t = np.arange(0, n_samples / fs, 1/fs)   # Adjusted time vector

        # Prepare figure and axis grid
        fig = plt.figure(figsize=(24, 9))
        gs = fig.add_gridspec(
            n_rows, 2, width_ratios=[2, 1], wspace=-0.2
        )  # Width ratio set to 2:1

        suffix_map = {
            "tcp": "- TCP-Referential Montage 1-25Hz Bandpass Filter",
            "cz": "- Cz-Referential Montage 1-25Hz Bandpass Filter",
            "le": "1-25Hz Bandpass Filter",
            "btm": "- Bipolar Transverse Montage 1-25Hz Bandpass Filter",
            "blm": "- Bipolar Longitudinal Montage 1-25Hz Bandpass Filter",
        }

        channel_suffix_map = {
            "tcp": "",
            "cz": "-Cz",
            "le": "-A1A2",
            "btm": "",
            "blm": "",
        }

        channels = epochs.pick_types(eeg=True).ch_names
        if ref not in ("tcp", "blm", "btm"):
            epochs = epochs.reorder_channels(new_order)
            channels = epochs.pick_types(eeg=True).ch_names
        channels = [i + channel_suffix_map[ref] for i in channels]

        plot_title = f"{rec_date} {suffix_map[ref]}"

        fig.text(
            0.14,
            0.99,
            plot_title,
            fontsize=34,
            fontweight="bold",
            va="top",
            ha="left",
            **{"fontname": "DejaVu Sans"},
        )

        dr = (dmax - dmin) * 0.7  # Crowd them a bit.
        y0 = dmin
        y1 = (n_rows - 1) * dr + dmax
        offsets = np.zeros((n_rows, 2), dtype=float)
        offsets[:, 1] = np.linspace(y0, y1, n_rows)

        # Reverse the array
        # data = np.flip(data, axis=0)  # Reverse the order of the data

        linecolor = "slategray"

        # Create subplot for each channel
        for i in range(n_rows):
            # Time series plot
            ax_time = fig.add_subplot(gs[i, 0])
            pos = ax_time.get_position()
            pos.x1 = 0.7  # adjust right end
            ax_time.set_position(pos)
            ax_time.plot(t, data[i, :] + offsets[i, 1], color="k")

            for s in np.arange(event_start, event_start + n_seconds):
                ax_time.axvline(s, 0, 1, color=linecolor, linestyle="--", alpha=0.75)

            eeg_scale = round(np.max(data[i, :]), 1)
            if i == n_rows - 1:
                ax_time.set_xlabel("Time (s)")
                ax_time.set_yticks([])
            else:
                ax_time.set_xticks([])
                ax_time.set_yticks([])
                ax_time.set_yticklabels([])

            # Makes time series amplitude text dyanmic with the width of the plot
            text_adjust = 20 / n_seconds

            # remove borders, axis ticks, and labels
            ax_time.set_yticklabels([])
            ax_time.set_ylabel("")
            ax_time.text(
                event_start + tmin - 0.6 / text_adjust,
                offsets[i][1],
                channels[i],
                fontweight="regular",
                fontsize=9,
                ha="center",
                **{"fontname": "DejaVu Sans"},
            )
            ax_time.text(
                event_start + tmax + 0.50 / text_adjust,
                offsets[i][1],
                f"{eeg_scale} µV",
                fontweight="regular",
                fontsize=8,
                ha="center",
                **{"fontname": "DejaVu Sans"},
            )
            # set x-axis formatter for ax_time
            ax_time.xaxis.set_major_formatter(FuncFormatter(format_func))
            ax_time.yaxis.set_label_coords(-0.05, 0.5)  # Adjust label position

            ax_time.spines["top"].set_visible(False)
            ax_time.spines["right"].set_visible(False)
            ax_time.spines["bottom"].set_visible(i == n_rows - 1)
            ax_time.spines["left"].set_visible(False)

        for i in range(n_rows):
            # Calculate FFT and plot using Welch's method
            freqs, psd = self.freqs, self.psds[epoch_id][i]

            # idx = np.where(freqs > 2.2)

            # freqs = freqs[idx]
            # psd = psd[:,idx]

            psd = smooth_psd(psd, window_len=2)

            # Select the range of frequencies of interest
            psd_range = psd[(freqs >= 2.2) & (freqs <= 25)]

            # FFT plot
            ax_fft = fig.add_subplot(gs[i, 1])
            pos = ax_fft.get_position()
            pos.x0 = 0.7  # adjust left start
            ax_fft.set_position(pos)

            ax_fft.fill_between(
                freqs, psd, color="#00FFFF"
            )  #  "#00ffff" # fill the area under the graph
            ax_fft.plot(freqs, psd, color="#000000", linewidth=1.5)  # 000000
            ax_fft.set_xlim([0.75, 25])
            ax_fft.set_ylim([0, psd_range.max()])

            ax_fft.axvline(4, 0, 1, color=linecolor, linestyle="--", alpha=0.75)
            ax_fft.axvline(8, 0, 1, color=linecolor, linestyle="--", alpha=0.75)
            ax_fft.axvline(13, 0, 1, color=linecolor, linestyle="--", alpha=0.75)

            psd_ylimit = psd_range.max()

            psd_ylimit = round(psd_ylimit, 1)

            if i == 0:
                ax_fft.text(
                    1.00,
                    0.95,
                    "\u03BCV\u00B2/Hz",
                    verticalalignment="top",
                    horizontalalignment="left",
                    transform=ax_fft.transAxes,
                    fontsize=9,
                    bbox=dict(facecolor="none", edgecolor="none", boxstyle="square"),
                )

            ax_fft.text(
                26.5,
                0,
                f"{psd_ylimit}",
                fontweight="regular",
                fontsize=8,
                ha="center",
                **{"fontname": "DejaVu Sans"},
            )

            if i == n_rows - 1:
                ax_fft.set_xlabel("Frequency (Hz)")
                ax_fft.set_yticks([])
                ax_fft.set_xticks(np.arange(2, 25, 2))
            else:
                ax_fft.set_xticks([])
                ax_fft.set_yticks([])

            ax_fft.spines["top"].set_visible(False)
            ax_fft.spines["right"].set_visible(False)
            ax_fft.spines["bottom"].set_visible(i == n_rows - 1)
            ax_fft.spines["left"].set_visible(False)

            spines = ["top", "right", "left", "bottom"]
            for s in spines:
                ax_time.spines[s].set_visible(False)
                ax_fft.spines[s].set_visible(False)

        # gs.update(wspace= -0.2, hspace= 0)
        plt.tight_layout()
        # plt.savefig(save)
        st.pyplot(fig)

    def plot_3d_psd(self):
        # Prepare data for 3D plot
        freqs = self.freqs
        epochs = range(self.psds.shape[0])
        psd_data = self.psds.mean(axis=1)  # Averaging across channels
        alpha_scores = self.data.index.values

        # Create a 3D plot
        fig = go.Figure()

        # Filter frequencies between 4 Hz and 20 Hz
        freq_mask = (freqs >= 2.2) & (freqs <= 20)
        filtered_freqs = freqs[freq_mask]
        filtered_psd_data = psd_data[:, freq_mask]

        # Create a meshgrid for x and y
        X, Y = np.meshgrid(filtered_freqs, epochs)

        # Stack the Z values (PSD data)
        Z = np.vstack(filtered_psd_data)

        # Create the surface plot
        surface = go.Surface(
            x=X, y=Y, z=Z,
            surfacecolor=np.tile(alpha_scores, (len(filtered_freqs), 1)).T,
            colorscale='ice',
            cmin=0, cmax=np.max(alpha_scores)
        )

        fig.add_trace(surface)

        fig.update_layout(
            title="3D PSD Plot Across All Epochs",
            scene=dict(
                xaxis_title='Frequency (Hz)',
                yaxis_title='Epochs',
                zaxis_title='PSD (uV^2/Hz)',
                xaxis=dict(range=[2.2, 20]),
                zaxis=dict(range=[0, 100])
            ),
            width=1200,
            height=1200
        )

        return fig


def format_func(value, tick_number):
    # convert second to minute and second, return as string 'mm:ss'
    mins, secs = divmod(int(value), 60)
    return f"{mins:02}:{secs:02}"


def smooth_psd(psd, window_len=10):
    """Smooth the PSD data using a moving average.

    Parameters
    ----------
    psd : 1-D array
        Power spectral density data.
    window_len : int, optional
        The length of the smoothing window.

    Returns
    -------
    smoothed_psd : 1-D array
        Smoothed PSD data.
    """
    window = np.ones(int(window_len)) / float(window_len)
    smoothed_psd = np.convolve(psd, window, "same")

    return smoothed_psd


def get_power(psd, freqs, f_range=[8, 13]):
    """Calculate the ratio between a frequency range and total (0-100 Hz)
    area under the curve.

    :param psd: (numpy.ndarray) power spectral densities.
    :param freqs: (numpy.ndarray) frequencies
    :return: delta relative power, expressed as a ratio.
    """

    fl, fh = f_range
    band_idx = np.where((freqs >= fl) & (freqs <= fh))[0]

    psd = psd * (10**12)
    band_power = simps(psd[:, band_idx], dx=freqs[1] - freqs[0])
    total_power = simps(psd, dx=freqs[1] - freqs[0])

    return sum(band_power / total_power)


def find_leads_off(raw, abs_offset_threshold=20, picks=["eeg"]):
    """Uses power spectrum analysis to detect which leads are bad (flat, artifact-heavy, high-frequency noise).
    Time series analysis of the EEG signal is used to determine poor connectivity.

    :param offset_threshold:
    :param raw:
    :return:
    """

    psds, freqs = mne.time_frequency.psd_welch(
        raw, picks=picks, n_overlap=params.N_OVERLAP
    )

    # An epoch object returns psds in three dimensions, this line ensures psds has the same shape if it was derived from a raw object.
    if len(psds.shape) == 3:
        psds = psds[0]

    # Use variance to determine and isolate bad channels.

    _, high_variance = variance_outliers(raw)

    # Fit a line to FFT. use the offset and the slope of the line to determine bad leads
    offsets, slopes = eeg_computational_library.get_offsets_slopes(
        psds, freqs, span=None
    )

    poor_connections = np.where(offsets > abs_offset_threshold)[0]

    nan_results = np.where(np.isnan(offsets))[
        0
    ]  # Leads should not be removed if polyfit fails, leads with high sync alpha and high offtsets are being thrown out. See koenig 3-26-2015

    flat_channels = np.where(np.absolute(offsets) < 0.01)[0]

    high_frequency_noise = np.where(slopes > 0)[0]

    results = {}
    ch_names = np.asarray(params.CHANNEL_ORDER)
    ch_names = np.delete(ch_names, -3, axis=0)  # remove ECG channel
    if (
        poor_connections.size != 0
        or nan_results.size != 0
        or flat_channels.size != 0
        or high_frequency_noise.size != 0
        or high_variance.size != 0
    ):
        leads_off_indices = np.unique(
            np.concatenate(
                (
                    poor_connections,
                    flat_channels,
                    nan_results,
                    high_frequency_noise,
                    high_variance,
                )
            )
        )

        leads_off = [ch_names[i] for i in leads_off_indices if i not in nan_results]

    else:
        leads_off_indices = np.empty((0,))
    if leads_off_indices.size == 0:
        return []
    leads_off = [ch_names[i] for i in leads_off_indices if i not in nan_results]
    return leads_off


def variance_outliers(raw):
    """Calculate variance for each EEG signal. Threshold was set to 3000,
    based on empirical obervation from testing across Wave Neuro and NYU datasets.

    params:
        raw (mne): raw mne object.

    returns:
        array: index positions of high variance outliers.
    """
    eeg = raw.get_data(picks="eeg", units="uV")
    variance = np.var(eeg, axis=2)
    threshold = 3000
    idx = np.where(variance > threshold)[1]

    return variance.tolist(), idx


def grade_alpha(score, all_scores):
    """
    Assign a letter grade based on where the score ranks within all_scores using percentiles.

    Args:
    - score (float): The score for which you want to determine the grade.
    - all_scores (list of float): List of all scores to determine the percentiles.

    Returns:
    - grade (str): The letter grade.
    """

    A_threshold = np.percentile(all_scores, 85)
    B_threshold = np.percentile(all_scores, 70)
    C_threshold = np.percentile(all_scores, 60)
    D_threshold = np.percentile(all_scores, 50)
    E_threshold = np.percentile(all_scores, 40)

    if score >= A_threshold:
        grade = "A"
    elif score >= B_threshold:
        grade = "B"
    elif score >= C_threshold:
        grade = "C"
    elif score >= D_threshold:
        grade = "D"
    elif score >= E_threshold:
        grade = "E"
    else:
        grade = "F"

    return grade


def bipolar_transverse_montage(raw):
    """Set the EEG reference to Bipolar Transverse Montage (BLM).

    params:
        raw (mne object): Original raw instance.
    returns
        raw (mne object): Re-referenced raw instance.
    """
    # Define anodes and cathodes for a longitudinal montage
    anode = [
        "F7",
        "Fp1",
        "Fp2",
        "F7",
        "F3",
        "Fz",
        "F4",
        "T3",
        "C3",
        "Cz",
        "C4",
        "T5",
        "P3",
        "Pz",
        "P4",
        "T5",
        "O1",
        "O2",
    ]
    cathode = [
        "Fp1",
        "Fp2",
        "F8",
        "F3",
        "Fz",
        "F4",
        "F8",
        "C3",
        "Cz",
        "C4",
        "T4",
        "P3",
        "Pz",
        "P4",
        "T6",
        "O1",
        "O2",
        "T6",
    ]

    # Set bipolar reference
    btm_raw = mne.set_bipolar_reference(raw, anode, cathode)
    btm_raw = btm_raw.pick_channels(CHANNEL_ORDER_BIPOLAR_TRANSVERSE)

    return btm_raw


CHANNEL_ORDER_BIPOLAR_TRANSVERSE = (
    "F7-Fp1",
    "Fp1-Fp2",
    "Fp2-F8",
    "F7-F3",
    "F3-Fz",
    "Fz-F4",
    "F4-F8",
    "T3-C3",
    "C3-Cz",
    "Cz-C4",
    "C4-T4",
    "T5-P3",
    "P3-Pz",
    "Pz-P4",
    "P4-T6",
    "T5-O1",
    "O1-O2",
    "O2-T6",
)
