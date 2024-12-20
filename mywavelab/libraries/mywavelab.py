
from copy import deepcopy
import datetime
from datetime import datetime as DateTime
import pprint

from ..io import eeg_pathing
from ..parsers.deymed import Deymed
from ..parsers.edf import Edf
from ..dsp.ecg_stats import calc_ecg_stats


class MyWaveLab:
    """
    Wraps a raw mne object
    """

    def __init__(self, file_path="", with_eeg=None, dob=None, show=False):
        self.parsed_data = None
        self.eeg = None
        self.recording_date = None
        self.recording_duration = None
        self.dob = dob
        self.ecg_data = None
        self.show = show

        # An mne object is not used at initialization, expects a file path then
        if with_eeg is None:
            self.file_str, self.file_path = eeg_pathing.get_clean_paths(file_path)
            self.eeg_ext = self.file_path.suffix
            self.read()
            if dob is not None: 
                self.age, self.subject_age = self.calculate_age(self.dob, self.recording_date)
            if show: self.show_parsed_data()
        
        # Else if an eeg is used at initialization
        else: self.eeg = with_eeg


    def read(self):
        """
        Read the EEG
        """
        try:
            if self.eeg_ext.lower() == ".dat":
                self.parsed_data = Deymed(self.file_str)
            elif self.eeg_ext.lower() == ".edf":
                self.parsed_data = Edf(self.file_str)
            else:
                raise ValueError("Unknown EEG Type")
            
            self.eeg = self.parsed_data.data
        except Exception as e:
            raise Exception(f"EEG failed in parser due to: {str(e)}")
        
        dt_object = self.eeg.info["meas_date"]
        if dt_object:
            self.recording_date = dt_object.strftime("%Y-%m-%d")
        else:
            self.recording_date = None
        try:
            self.recording_duration = self.eeg.times[-1]
        except IndexError:
            raise AttributeError("EEG file has no EEG data")
        
        try:
            pass
            
        except Exception as e:
            print(str(e))



    def ecg_stats(self, store=True):
        """
        Gets HRV statistic data for both Linked-ears and Cz referenced ECG data.
        """
        
        hrv_stats_dict = {
            "a1a2": {}, "cz": {},
        }

        try: 
            # For each montage/ key in hrv_stats_dict
            for montage in hrv_stats_dict.keys():
                temp_eeg = self.eeg.copy()
                ecg_ch_names = temp_eeg.copy().pick_types(ecg=True).ch_names

                mapping = {ch_name: 'eeg' for ch_name in ecg_ch_names}
                temp_eeg.set_channel_types(mapping)

                if montage == "cz": temp_eeg.set_eeg_reference(['Cz'])
                ecg_chs_data = temp_eeg.get_data(picks=ecg_ch_names)

                # For each available ECG channel
                for i, each_ecg_array in enumerate(ecg_chs_data):
                    ecg_data = calc_ecg_stats(
                        each_ecg_array, 
                        temp_eeg.info['sfreq'], 
                        store, 
                    ) 
                    hrv_stats_dict[montage][ecg_ch_names[i]] = ecg_data


            if store: self.ecg_data = hrv_stats_dict

            return hrv_stats_dict 
            
        except Exception as e:
            print(str(e))
            if store: self.ecg_data = hrv_stats_dict

            return hrv_stats_dict 



    def calculate_age(self, dob, date):
        """
        Calculates the age of the patient in the eeg at the time of the recording, 
        using the patient's birthday if available and the recording date of the eeg.

        """

        try:
            meas_date = DateTime.strptime(date, "%Y-%m-%d")
        except TypeError as Error:
            print(Error)

        try:
            dob_dt = DateTime.strptime(dob, "%Y-%m-%d")
        except ValueError as Error:
            print(Error)
        except TypeError as Error:
            print(Error)

        age_td = meas_date - dob_dt
        year = datetime.timedelta(days=365)
        age = age_td // year
        age = int(age)
        subject_age = age_td / year

        return age, subject_age



    def show_parsed_data(self):
        """
        Get some feedback from the read data.
        """
        print(f"\n=== Parsed EEG Data =======================================")
        print(self.eeg.info)
        print("-----------------------------------------------------------")
        print(f"Channels: {self.parsed_data.ch_names}")
        print(f"===========================================================\n")



    def copy(self):
        return deepcopy(self)