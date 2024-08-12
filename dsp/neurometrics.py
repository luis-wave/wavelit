import numpy as np
from scipy.integrate import simps


def get_power(psd, freqs, f_range=[8, 13]):
    """Calculate the ratio between a frequency range and total (0-100 Hz)
    area under the curve.

    :param psd: (numpy.ndarray) power spectral densities.
    :param freqs: (numpy.ndarray) frequencies
    :return: delta relative power, expressed as a ratio.
    """

    channel_order_eeg = (
            "Fp1", "Fp2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2",
            "F7", "F8", "T3", "T4", "T5", "T6", "Fz", "Cz", "Pz"
        )

    selected_channels = ["Fp1","Fp2","F3", "F4","T5", "T6", "P3", "P4", "O1", "O2", "Fz", "Pz"]

    selected_indices = [channel_order_eeg.index(channel) for channel in selected_channels]

    psd = psd[selected_indices, :]


    fl, fh = f_range
    band_idx = np.where((freqs >= fl) & (freqs <= fh))[0]
    total_band_idx = np.where((freqs >= 2.2) & (freqs <= 25))[0]

    band_power = simps(psd[:, band_idx], dx=freqs[1] - freqs[0])
    total_power = simps(psd[:, total_band_idx], dx=freqs[1] - freqs[0])

    band_power = band_power[band_power!=0]
    total_power = total_power[total_power!=0]

    return sum(band_power / total_power)