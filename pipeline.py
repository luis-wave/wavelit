import logging
import mne

from matplotlib.collections import LineCollection
from matplotlib.ticker import AutoLocator, FuncFormatter, MultipleLocator
from mywaveanalytics.libraries import (
    filters,
    references,
)

from mywaveanalytics.utils.params import ELECTRODE_GROUPING

import numpy as np
import pandas as pd

from scipy.integrate import simps
from scipy.signal import welch, find_peaks, peak_prominences

log = logging.getLogger(__name__)


class PersistPipeline:
    def __init__(self, mw_object, time_win=20, ref="le"):
        self.mw_object = mw_object.copy()
        self.sampling_rate = mw_object.eeg.info["sfreq"]
        self.epochs = self.preprocess_data(time_win=time_win, ref=ref)
        self.freqs, self.psds = self.calculate_psds()

        # Flatten psds for DataFrame storage
        flattened_psds = self.psds.reshape(self.psds.shape[0], -1)  # Flattening epochs, channels, and frequency bins

        self.data = pd.DataFrame({
            "flattened_psds": list(flattened_psds)  # Store flattened psds
        })

        # Reshape and calculate scores
        self.data['score'] = self.data['flattened_psds'].apply(
            lambda flattened_psd: self.get_total_sync_score(self.freqs, np.reshape(flattened_psd, self.psds.shape[1:]))
        )

        # Sort the DataFrame by score in descending order
        self.data = self.data.sort_values(by='score', ascending=False)

    def preprocess_data(self, time_win=20, ref=None):
        filters.eeg_filter(self.mw_object, 1, None)
        filters.notch(self.mw_object)
        filters.resample(self.mw_object)

        raw = self.mw_object.eeg

        if ref == "tcp":
            raw = references.temporal_central_parasagittal(self.mw_object)
        if ref == "cz":
            raw = references.centroid(self.mw_object)

        epochs = mne.make_fixed_length_epochs(raw, duration=time_win, preload=True, overlap=time_win - 1)
        return epochs

    def calculate_psds(self):
        time_series_eeg = self.epochs.get_data(picks="eeg", units="uV")
        freqs, psds = welch(time_series_eeg, self.sampling_rate)
        return freqs, psds

    def get_total_sync_score(self, eeg_frequencies, power_spectral_density):
        alpha_range = (8, 13)
        frequency_prominence_products = []
        for channel_powers in power_spectral_density:
            alpha_mask = (eeg_frequencies >= alpha_range[0]) & (eeg_frequencies <= alpha_range[1])
            alpha_frequencies = eeg_frequencies[alpha_mask]
            alpha_powers = channel_powers[alpha_mask]
            peaks, _ = find_peaks(alpha_powers)
            if not peaks.size:
                continue
            prominences = peak_prominences(alpha_powers, peaks)[0]
            frequency_prominence_products.extend(alpha_frequencies[peaks] * prominences)
        return np.median(frequency_prominence_products) if frequency_prominence_products else 0