import mne
import numpy as np
from mywaveanalytics.libraries import eeg_computational_library
from mywaveanalytics.utils import params


def find_leads_off(raw, abs_offset_threshold=35, picks=["eeg"]):
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

    nan_results = np.where(
        np.isnan(offsets)
    )[
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
