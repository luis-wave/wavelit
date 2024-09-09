import streamlit as st

from pathlib import Path
import pandas as pd
import numpy as np

from scipy.signal import find_peaks
from scipy import signal
import mne

from mywaveanalytics.libraries import mywaveanalytics as mwa
from mywaveanalytics.libraries import (
    # database,
    # eeg_artifact_removal,
    filters,
    # eeg_computational_library,
    # ecg_statistics,
    #clinical,
    #consumer_statistics,
    references
    # protocol,
)



"""
Load the EEG data from a file
"""
# @st.cache_data
def get_data_from_file_path(path, get_dict=False, picks=None):
    ext = str(Path(path).suffix)

    if ext.lower() == ".dat": eeg_type = 0
    elif ext.lower() == ".edf": eeg_type = 1

    mw_object = mwa.MyWaveAnalytics(f_path=path, eeg_type=eeg_type)
    raw_mwa = mw_object.eeg

    # raw_mwa = apply_waev_filter(raw_mwa, lowf=0.5)
    raw_mwa, _ = apply_fir_filter(
        raw_mwa, 
        fs=raw_mwa.info['sfreq'], 
        zero_phase_delay=True, 
        filter_eog=False
    )

    raw_mwa = raw_mwa.resample(128.0)
    # raw_np = raw.get_data(picks=picks)

    if get_dict is True:
        eeg_dict = get_referenced_data(raw_mwa)
        return eeg_dict
    else: 
        return raw_mwa
    
"""
Load the EEG data from mwa object
"""
# @st.cache_data
def get_data_from_mw_object(mw_object, get_dict=False, resample=128.0, picks=None, scale_df=False):
    print(f"Getting data for montages...")
    apply_waev_filter(
        mw_object=mw_object, 
        lowf=None, 
        highf=None, 
        default_time_constant=True,
    )
    raw_mwa = mw_object.eeg
    

    # raw_mwa = apply_waev_filter(raw_mwa, lowf=0.5)
    raw_mwa, _ = apply_fir_filter(
        raw_mwa, 
        fs=raw_mwa.info['sfreq'], 
        zero_phase_delay=True, 
        filter_eog=False
    )

    raw_mwa = raw_mwa.resample(resample)
    # raw_np = raw.get_data(picks=picks)

    if get_dict is True:
        eeg_dict = get_referenced_data(raw_mwa, scale_df=scale_df)
        return eeg_dict
    else: 
        return raw_mwa

"""
All EEG data needed
"""

def get_referenced_data(raw_mwa=None, scale_df=False):
    if raw_mwa is not None:
        raw_a1a2 = order_montage_channels(raw_mwa.copy(), "a1a2")
        raw_cz = order_montage_channels(references.centroid(raw_mwa.copy()), "cz")
        raw_bpt = bipolar_transverse(raw_mwa.copy())
        raw_tcp = references.temporal_central_parasagittal(raw_mwa.copy())
        raw_avg = order_montage_channels(references.average(raw_mwa.copy()), "avg")
        raw_ref = order_montage_channels(references.infinite_rest(raw_mwa.copy()), "ref")

        eeg_dict = dict(
            a1a2 = dict(
                raw = raw_a1a2,
                data = raw_a1a2.get_data(),
                df = scale_dataframe(raw_to_df(raw_a1a2)) if scale_df else raw_to_df(raw_a1a2),
                channels = raw_a1a2.info["ch_names"],
                times = raw_a1a2.times,
            ),
            cz = dict(
                raw = raw_cz,
                data = raw_cz.get_data(),
                df = scale_dataframe(raw_to_df(raw_cz)) if scale_df else raw_to_df(raw_cz),
                channels = raw_cz.info["ch_names"],
                times = raw_cz.times
            ),
            bpt = dict(
                raw = raw_bpt,
                data = raw_bpt.get_data(),
                df = scale_dataframe(raw_to_df(raw_bpt)) if scale_df else raw_to_df(raw_bpt),
                channels = raw_bpt.info["ch_names"],
                times = raw_bpt.times
            ),
            tcp = dict(
                raw = raw_tcp,
                data = raw_tcp.get_data(),
                df = scale_dataframe(raw_to_df(raw_tcp)) if scale_df else raw_to_df(raw_tcp),
                channels = raw_tcp.info["ch_names"],
                times = raw_tcp.times
            ),
            avg = dict(
                raw = raw_avg,
                data = raw_avg.get_data(),
                df = scale_dataframe(raw_to_df(raw_avg)) if scale_df else raw_to_df(raw_avg),
                channels = raw_avg.info["ch_names"],
                times = raw_avg.times
            ),
            ref = dict(
                raw = raw_ref,
                data = raw_ref.get_data(),
                df = scale_dataframe(raw_to_df(raw_ref)) if scale_df else raw_to_df(raw_ref),
                channels = raw_ref.info["ch_names"],
                times = raw_ref.times
            ),
        )

        return eeg_dict
    else: 
        raise Exception("get_referenced_data() requires raw mne (from mwa object) to be passed in")


"""
Reorder the montage channel order
"""
def order_montage_channels(raw=None, montage=None): 
    try: 
        new_order_all = ["Fz","Cz","Pz","Fp1","Fp2","F3","F4","F7","F8", 
                        "C3","C4","T3","T4","P3","P4","T5","T6","O1","O2",
                        "A1","A2", "ECG"
                        ]
        new_order_a1a2 = ["Fz","Cz","Pz","Fp1","Fp2","F3","F4","F7","F8", 
                        "C3","C4","T3","T4","P3","P4","T5","T6","O1","O2", 
                        "A1","A2"]
        new_order_ecg = ["Fz","Cz","Pz","Fp1","Fp2","F3","F4","F7","F8", 
                        "C3","C4","T3","T4","P3","P4","T5","T6","O1","O2","ECG"]
        new_order_eeg = ["Fz","Cz","Pz","Fp1","Fp2","F3","F4","F7","F8", 
                        "C3","C4","T3","T4","P3","P4","T5","T6","O1","O2"]
        
        remove_a1a2 = ["A1", "A2"]
        remove_cz = ["Cz"]
        non_eeg = ["ECG", "A1", "A2"]
        remove_ecg = ["ECG"]


        if set(["ECG", "A1", "A2"]).issubset(set(raw.info["ch_names"])):
            raw.reorder_channels(new_order_all)
        elif set(["A1", "A2"]).issubset(set(raw.info["ch_names"])):
            raw.reorder_channels(new_order_a1a2)
        elif set(["ECG"]).issubset(set(raw.info["ch_names"])):
            raw.reorder_channels(new_order_ecg)
        else:
            raw.reorder_channels(
                [channel for channel in new_order_eeg] # old condition: if channel not in remove_a1a2
            )

        
        # print(f"changing the labels of {montage} montage...")
        # Modify channel labels so the reference is displayed
        if montage == "a1a2":
            try: 
                raw.drop_channels(remove_a1a2)
            except:
                pass
            old_labels = raw.info["ch_names"]
            new_labels = {
                old_label: old_label + "-A1A2" for old_label in old_labels
            }
            raw.rename_channels(new_labels)
        elif montage == "cz":
            try: 
                raw.drop_channels(remove_cz)
                raw.drop_channels(remove_a1a2)
            except:
                pass
            old_labels = raw.info["ch_names"]
            new_labels = {
                old_label: old_label + "-Cz" for old_label in old_labels
            }
            raw.rename_channels(new_labels)
        elif montage == "avg":
            try: 
                raw.drop_channels(remove_a1a2)
            except:
                pass
            old_labels = raw.info["ch_names"]
            new_labels = {
                old_label: old_label + "-Avg" for old_label in old_labels
            }
            raw.rename_channels(new_labels)
        elif montage == "ref":
            old_labels = raw.info["ch_names"]
            new_labels = {
                old_label: old_label + "-Ref" for old_label in old_labels
            }
            raw.rename_channels(new_labels)

        return raw

    except Exception as e:
        print(f"ERROR: {e}")

    







"""
Convert an mne.io.Raw object to a pandas DataFrame

Parameters:
raw (mne.io.Raw): The raw object to convert

Returns:
pd.DataFrame: A DataFrame containing the time points and channel data
"""
def raw_to_df(raw=None):
    # Get data and times
    data = raw.get_data()  # shape (n_channels, n_times)
    times = raw.times  # shape (n_times,)
    
    # Create a DataFrame
    df = pd.DataFrame(data.T, columns=raw.ch_names)
    
    # Add the time columns
    df['time'] = times
    df['timestamp'] = pd.to_datetime(df['time'], unit='s').apply(lambda x: x.strftime('%H:%M:%S.%f')[:-3])
    
    # Reorder columns to place 'Time' first
    # Reorder columns to place 'time' first and 'timestamp' second
    cols = df.columns.tolist()
    cols = ['time', 'timestamp'] + [col for col in cols if col not in ['time', 'timestamp']]
    df = df[cols]
    
    return df


@st.cache_data
def scale_dataframe(df):
    # separate the 'Time' column
    try: times_col = df['time']
    except: pass
    try: timestamps_col = df['timestamp']
    except: pass

    # identify ECG and EEG columns
    try: 
        ecg_columns = df.filter(like='ECG').columns
        eeg_columns = df.columns.difference(ecg_columns).difference(['time', 'timestamp'])
    except:
        eeg_columns = df.columns

    # function to find local maxima and minima
    def find_extrema(signal):
        peaks, _ = find_peaks(signal)
        troughs, _ = find_peaks(-signal)
        return peaks, troughs

    # Function to return min/max stats for the eeg based on peaks and troughs
    def get_min_max_stats(columns, df):
        # calculate the median of maxima and minima for each EEG channel
        median_max_values = []
        median_min_values = []
        mean_max_values = []
        mean_min_values = []

        # get the peaks and the troughs
        for col in columns:
            peaks, troughs = find_extrema(df[col])
            max_values = df[col].iloc[peaks]
            min_values = df[col].iloc[troughs]
            if len(max_values) > 0:
                median_max_values.append(max_values.median())
                mean_max_values.append(max_values.mean())
            if len(min_values) > 0:
                median_min_values.append(min_values.median())
                mean_min_values.append(min_values.mean())

        # calculate the max of the above 0 median peaks and the min of the below 0 median troughs
        median_max = np.max(median_max_values)
        median_min = np.min(median_min_values)
        mean_max = np.max(mean_max_values)
        mean_min = np.min(mean_min_values)

        return median_max, median_min, mean_max, mean_min

    median_max, median_min, mean_max, mean_min = get_min_max_stats(eeg_columns, df)

    # scale the EEG columns
    df_eeg = df[eeg_columns]

    # new norm: scale to -1, 1 and then adjust it to a percentage of
    bound = (median_max + abs(median_min)) / 2
    scaled_eeg = (df_eeg / bound) * 0.1

    try: 
        # scale ECG column(s) separately
        median_max, median_min, mean_max, mean_min = get_min_max_stats(ecg_columns, df)

        df_ecg = df[ecg_columns]
        
        # new norm: scale to -1, 1 and then adjust it to a percentage of
        bound = (median_max + abs(median_min)) / 2
        scaled_ecg = (df_ecg / bound) * 0.05

        # reattach the 'time' column and combine scaled columns
        try: scaled_df = pd.concat([times_col, timestamps_col, scaled_ecg, scaled_eeg], axis=1)
        except: scaled_df = pd.concat([times_col, scaled_ecg, scaled_eeg], axis=1)

    except:
        # reattach the 'time' column and combine scaled columns
        try: scaled_df = pd.concat([times_col, timestamps_col, scaled_eeg], axis=1)
        except: scaled_df = pd.concat([times_col, scaled_eeg], axis=1)

    return scaled_df


"""
Low filter units: Time constant in seconds
0.08 sec is roughly equivalent to a 1.9894 Hz cuttoff frequency

highpass filter to remove signal drift e.g. : (low val=  0.50, high val = None)
"""
def apply_waev_filter(mw_object=None, 
                      time_constant=0.08, 
                      lowf=None, 
                      highf=None, 
                      default_time_constant=False,
                      ):
    
    if lowf is None and highf is None:
        # print(f"Time constant used: {time_constant}")
        if default_time_constant:
            filters.eeg_filter(mw_object, 1.9894, None)
        else: 
            raise Exception("Time constant low filter in progress (from sec)")
    else:
        filters.eeg_filter(mw_object, lowf, highf) 


"""
Funcion that takes a 1d or 2d array of data and applies a 1-25 Hz FIR filter
"""
def apply_fir_filter(data=[], fs=128.0, cutoff_freq=13, bandwidth=24, numtaps=200, window='blackman', zero_phase_delay=True, filter_eog=False, display_eog_data=False):
    lowcut = cutoff_freq - bandwidth / 2
    if lowcut < 0: lowcut = 0

    highcut = cutoff_freq + bandwidth / 2
    
    # design the filter
    coeffs = signal.firwin(numtaps, [lowcut, highcut], pass_zero=False, fs=fs, window=window)
    
    # check the type of 'data'
    if isinstance(data, np.ndarray):
        if data.ndim == 1:
            if zero_phase_delay: filtered_data = signal.filtfilt(coeffs, 1.0, data)
            else: filtered_data = signal.lfilter(coeffs, 1.0, data)
        elif data.ndim == 2:
            if zero_phase_delay:
                filtered_data = np.apply_along_axis(lambda m: signal.filtfilt(coeffs, 1.0, m), axis=0, arr=data)
            else:
                filtered_data = np.apply_along_axis(lambda m: signal.lfilter(coeffs, 1.0, m), axis=0, arr=data)
        else:
            raise ValueError("Unsupported data shape for numpy array. Please provide 1D or 2D array.")
        
        return filtered_data, coeffs
    
    elif isinstance(data, mne.io.BaseRaw):
        # get the data and apply the filter
        original_data = data.get_data()
        
        if zero_phase_delay:
            filtered_np = np.apply_along_axis(lambda m: signal.filtfilt(coeffs, 1.0, m), axis=1, arr=original_data)
        else: 
            filtered_np = np.apply_along_axis(lambda m: signal.lfilter(coeffs, 1.0, m), axis=1, arr=original_data)
        
        # create a new MNE Raw object with the filtered data
        filtered_data = mne.io.RawArray(filtered_np, data.info)
        
        if filter_eog:
            pass

        return filtered_data, coeffs
    
    else:
        raise TypeError("Unsupported data type. Acceptable types: np.ndarray, mne.io.BaseRaw")

# Resample the data in an mne raw object
def eeg_resample(data=None, freq=100): 
    # data.load_data()
    return data.resample(freq)

# Function that calculates the power spectrum and associated frequencies for a 1d or 2d array of data



# function that smooths a 1d or 2d array of power spectrum data for associated frequencies



"""
Returns helpful values for setting the y axis placement for each channel for display
"""
def get_viewer_format_values(raw=None):
    num_channels = len(raw.info["ch_names"])

    # the range sets the y axis
    range = (-0.5, num_channels-0.5)
    format_dict = dict(
        y_range = range,
        num_channels = num_channels,
        y_bottom_coordinate = 0,
        y_top_coordinate = num_channels-1,
    )

    return format_dict


def bipolar_transverse(raw) :
    # bipolar-transverse montage electrodes
    ANODES =    ['F7',
                'Fp1',
                'Fp2',
                'F7',
                'F3',
                'Fz',
                'F4',
                'T3',
                'C3',
                'Cz',
                'C4',
                'T5',
                'P3',
                'Pz',
                'P4',
                'T5',
                'O1',
                'O2']

    CATHODES =  ['Fp1',
                'Fp2',
                'F8',
                'F3',
                'Fz',
                'F4',
                'F8',
                'C3',
                'Cz',
                'C4',
                'T4',
                'P3',
                'Pz',
                'P4',
                'T6',
                'O1',
                'O2',
                'T6']
    
    # change the names of the mne raw channel names (i.e. Fp1-A1A2 -> Fp1)
    raw.rename_channels(lambda channel: channel.split('-')[0])

    # create bipolar transverse reference (BPT)
    raw_bpt = mne.set_bipolar_reference(raw, anode=ANODES, cathode=CATHODES)

    # remove irrelevant channels
    channels =  [channel 
                 for channel in raw_bpt.info['ch_names'] 
                 if "-" in channel
                 ]

    # replace with relevant channels/data
    raw_bpt.pick_channels(channels)

    return raw_bpt


# take the plot timestamps and make them more readable
def reformat_timestamps(timestamps):
    def format_time(ts):
        if isinstance(ts, str):
            if ts.startswith('00:'):
                return ts[3:8]  # Remove "00:" from the start (keep "MM:SS")
            else:
                return ts[:8]  # Keep only "HH:MM:SS"
        else:
            return ts
    
    if isinstance(timestamps, pd.DataFrame):
        formatted = timestamps.applymap(format_time).stack().unique()
    elif isinstance(timestamps, np.ndarray):
        formatted = np.unique(np.vectorize(format_time)(timestamps))
    elif isinstance(timestamps, list):
        formatted = sorted(set(format_time(ts) for ts in timestamps))
    else:
        raise TypeError("Input must be a DataFrame, NumPy array, or list")
    
    return sorted(formatted)