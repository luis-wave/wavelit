import numpy as np
from scipy.signal import windows

"""
Functions taken directly from MyWaveReporting library.
Will be applied to keep PSD graphs consistent across Wave Neuro spectral data.
"""


def preprocessing(d, freqs, lf_cutoff=2.2):
    """Convert to microvolts, apply taper, apply rolling window, apply lf_cutoff"""
    d = convert_to_microvolts(d)
    d = rolling_window(d)
    d, freqs = apply_cutoff(d, freqs, lf_cutoff=lf_cutoff)
    return d, freqs


def convert_to_microvolts(d):
    return (d * (10**12)) ** (1 / 2)


def rolling_window(d):
    window = windows.triang(2)
    return np.convolve(d, window, mode="same") / sum(window)


def apply_cutoff(d, freqs, lf_cutoff=2.2):
    mask = (freqs >= lf_cutoff) & (freqs <= 25)
    return d[mask], freqs[mask]
