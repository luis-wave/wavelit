import logging
import textwrap

import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.ticker import FuncFormatter
from mywaveanalytics.libraries import filters, references, ecg_statistics
from mywaveanalytics.pipelines import eqi_pipeline
from mywaveanalytics.utils.params import (DEFAULT_RESAMPLING_FREQUENCY,
                                          ELECTRODE_GROUPING)
from scipy.signal import find_peaks, peak_prominences, welch

from dsp.artifact_removal import find_leads_off
from dsp.neurometrics import get_power
from graphs.psd_epochs import psd_peaks_3d
from utils.graph_utils import smooth_psd
from utils.helpers import format_func, grade_alpha, grade_bads

log = logging.getLogger(__name__)


class StandardPipeline:
    def __init__(self, mw_object):
        self.mw_object = mw_object.copy()

    def run(self):
        with st.spinner("Calculate heart rate measures..."):
            self.calculate_heart_rate()

    def calculate_eqi(self):
        try:
            # Calculate EEG quality index
            pipeline = eqi_pipeline.QAPipeline(self.mw_object)
            pipeline.run()
            analysis = pipeline.analysis_json
            st.session_state.eqi = analysis["eqi_score"]
        except Exception as e:
            st.error(f"EEG quality assessment failed for the following reason: {e}")

    def calculate_heart_rate(self):
        try:
            ecg_events_loc = filters.ecgfilter(self.mw_object)

            # Find heart rate
            heart_rate_bpm, stdev_bpm = ecg_statistics.ecg_bpm(
                ecg_events_loc
            )
            st.session_state.heart_rate = round(heart_rate_bpm)
            st.session_state.heart_rate_std_dev = round(stdev_bpm, 2)
        except Exception as e:
            st.error(f"Heart rate calculation failed for the following reason: {e}")


class PersistPipeline:
    def __init__(self, mw_object):
        self.mw_object = mw_object.copy()
        self.ref = None
        self.sampling_rate = mw_object.eeg.info["sfreq"]
        self.epochs = None
        self.freqs = None
        self.psds = None
        self.data = None

    def reset(self, mw_object):
        self.mw_object = mw_object.copy()
        self.ref = None
        self.sampling_rate = mw_object.eeg.info["sfreq"]
        self.epochs = None
        self.freqs = None
        self.psds = None
        self.data = None

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

        self.data["bads"] = [
            find_leads_off(self.epochs[i]) for i in range(len(self.epochs))
        ]

        self.data["n_bads"] = self.data["bads"].apply(lambda x: len(x))

        self.data["graded_bads"] = self.data["n_bads"].apply(lambda x: grade_bads(x))

        # Sort the DataFrame by score in descending order
        self.data = self.data.sort_values(
            by=["graded_bads", "alpha"], ascending=[True, False]
        )

    def generate_graphs(self):
        graph_df = self.data.copy()

        graph_df = graph_df[graph_df["sync_score"] < 200]

        for idx in graph_df.index[:20]:
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

        bads = self.data["bads"][epoch_id]

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

        if bads:
            epochs = epochs.drop_channels(bads)
            new_order = [item for item in new_order if item not in bads]

        epochs = epochs.reorder_channels(new_order)

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

        if bads:
            plot_title = plot_title + f" ({', '.join(bads)} removed)"

            # Wrap title if it's too long
            wrapper = textwrap.TextWrapper(width=60)  # Adjust 'width' to your needs
            plot_title = "\n".join(wrapper.wrap(plot_title))

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
            freqs, psd = welch(data[i], fs=fs)

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
                    "\u03bcV\u00b2/Hz",
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

        excess_sync_score = self.data["sync_score"] > 150

        # Filter frequencies between 4 Hz and 20 Hz
        freq_mask = (freqs >= 2.2) & (freqs <= 20)
        filtered_freqs = freqs[freq_mask]
        filtered_psd_data = psd_data[:, freq_mask]

        # Set indices of filtered_psd_data where sync_score is over 150 to 0
        filtered_psd_data[excess_sync_score, :] = 0

        return psd_peaks_3d(filtered_freqs, filtered_psd_data, epochs, alpha_scores)
