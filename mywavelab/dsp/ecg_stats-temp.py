import numpy as np
import pyedflib
import pandas as pd
import subprocess
import json
from ecgdetectors import Detectors
import hrv
import mne
from digital_filters import clean_date
from pathlib import Path
from scipy import signal
import os
import datetime


local_jib_path = Path.cwd() / 'JIBStandalone.exe' #r"C:\Users\lcamargo\JIBStandalone.exe"    #replace with your local path for JIBStandalone.exe

class EEG:
    def __init__(self, filename):
        self._filename = filename
        self.header = {}

        extension = filename.split(".")[-1].lower()
        if 'dat' in extension:

            filename = filename.strip('"') #removes quotation marks from filepath input,
            
            with open(filename, "rb") as f:
                #Header
                self.header["PID"] = f.read(12).decode('utf-8')
                self.header["last name"] = f.read(16).decode('utf-8').strip().title().split('\x00',1)[0]
                self.header["first name"] = f.read(12).decode('utf-8').strip().title().split('\x00',1)[0]
                self.header["recording date"] = clean_date(f.read(12).decode('utf-8').strip().split('\x00',1)[0])
                rec_time = f.read(8).decode('utf-8')
                sampling_rate = ord(f.read(1))


                f.seek(1,1)

                if sampling_rate == 0: #if sampling rate is 0, need to go back and ready two bytes as an integer, real sampling frequnecy (fs) > 256 Hz.
                    f.seek(-2,1)
                    sampling_rate = int.from_bytes(f.read(2), "little")



                channels_count = ord(f.read(1))

                #Sensitivity
                #sensitivity = ord(f.read(1))
                f.seek(1,1)

                nChn = np.arange(channels_count, dtype = np.float64)

                mychannels = range(channels_count)
                channels = []

                for i in mychannels:
                    string = f.read(6).decode('utf-8').replace('\x00','').strip()
                    channels.append(string)

                channels = np.asarray(channels)
                channels[21] = 'EKG'



                self.header["sampling_rate"] = sampling_rate

                #skip to where all the signal data is stored.
                f.seek(512,0)
                data = np.fromfile(f, dtype = np.int16, count= -1)
                dat = data.size
                nRec = int(dat/channels_count)
                signals = np.reshape(data,(channels_count,nRec), order = 'F')

                self.data = pd.DataFrame(signals.T, columns=channels)
                self.channels = channels
                self.sampling_rate = sampling_rate

        elif 'eas' in extension:
            eas_filepath = filename
            csv_output_path = Path(filename[:-4] + ".csv")
            cwd = Path(os.getcwd())
            csv_output_path = cwd/str(csv_output_path.name)
#             print(csv_output_path)

            JIB_path = local_jib_path

            args = [JIB_path, "-file", eas_filepath, "-dumpcsv", csv_output_path]
            subprocess.Popen(args).wait()

            raw_data = pd.read_csv(r""+str(csv_output_path))
            _labels =  {label:label.strip() for label in raw_data.columns}
            data = raw_data.rename(columns = _labels )

            self.channels = data.columns
            self.data = data
            self.sampling_rate = 200
            self.header['sampling_rate'] = 200
            os.remove(csv_output_path)



        elif 'edf' in extension:
                raw = mne.io.read_raw_edf(filename) #opens EDF file object
                df = raw.to_data_frame().drop('time', axis=1)
                channels = df.columns

                if "EEG" in channels[0]:
                    channels = [label.replace('EEG ','') for label in channels]
                    channels = [label.replace('ECG','EKG') for label in channels]
                    channels = [label.replace('EKG1','EKG') for label in channels]



                df.columns = channels

                signals = df.values.T

                #Grab header information from EDF file object.
                if type(raw.info['meas_date']) is datetime.date:
                    self.header['recording date'] = raw.info['meas_date']
                elif type(raw.info['meas_date']) is datetime.datetime:
                    self.header['recording date'] = raw.info['meas_date'].date()
                else:
                    self.header['recording date'] = clean_date(raw.info['meas_date']).date()


                #header = [pid, last_name, first_name, recording_date, sample_rate]

                self.data = df
                self.channels = channels
                self.sampling_rate = raw.info['sfreq']
                self.header['sampling_rate'] = raw.info['sfreq']

        elif 'csv' in extension:
            self.data = pd.read_csv(filename)
            self.channels = self.data.columns
        elif 'eeg' in extension:
            with open(filename, 'rb') as f:
                wavi = f.read()
                wavi = wavi.replace(b"\r\n", b"")
                wavi_data = np.fromstring(wavi,dtype = int,  sep=" ")
                data_length = wavi_data.shape[0]
                channel_length = int(data_length/19)
                wavi_matrix = wavi_data.reshape(channel_length, 19)
                signals = wavi_matrix.T
                channels = ["Fp1", "Fp2", "F3", "F4", "F7", "F8", "C3", "C4", "P3","P4", "O1","O2", "T3","T4","T5","T6","Fz","Cz","Pz"]
                sampling_rate = 250
                self.data = pd.DataFrame(signals.T, columns=channels)
                self.channels = channels
                self.sampling_rate = sampling_rate
        else:
            filename = filename.split("/")[-1]
            raise Exception(f'Unable to read {filename}. Only EEG files with extensions DAT, EDF, EEG, CSV are supported.')

    def channels(self):
        return self.data.columns

    def to_numpy(self):
        return self.data.values.T

    def to_dict(self):
        return self.data.to_dict(orient = "list")
    
    def pan_peaks(self) :
        if "EKG" not in self.data.columns:
            raise Exception(f'File does not contain channel for electrocardiogram (EKG) data.')
        else:
            ekg = self.data['EKG'].values
            fs = self.sampling_rate

            detectors = Detectors(fs)

            qrs_i = detectors.pan_tompkins_detector(ekg)
            
        return qrs_i
    
    def ekg_data(self):
        if "EKG" not in self.data.columns:
            raise Exception(f'File does not contain channel for electrocardiogram (EKG) data.')
        else:
            ekg = self.data['EKG'].values
            fs = self.sampling_rate

            detectors = Detectors(fs)

            qrs_i = detectors.pan_tompkins_detector(ekg)
#             print("qrs_i: ")
#             print(qrs_i)
            hrv_measure = hrv.HRV(fs) #

            heart_rates = hrv_measure.HR(qrs_i) # calculates and stores instantaneous heart rates in an array

            heart_rate = round(np.mean(heart_rates),1) #average heart rate

            hr_std_dev = round(np.std(heart_rates),1) #standard deviation of heart rates

            RMSSD = round(hrv_measure.RMSSD(qrs_i),1)
            SDNN = round(hrv_measure.SDNN(qrs_i),1)
            SDSD = round(hrv_measure.SDSD(qrs_i),1)
            nn50 = hrv_measure.NN50(qrs_i)
            nn20 = hrv_measure.NN20(qrs_i)
            pNN50 = round(hrv_measure.pNN50(qrs_i)*100,1)
            pNN20 = round(hrv_measure.pNN20(qrs_i)*100,1)
            low_high_freq_ratio = round(hrv_measure.fAnalysis(qrs_i)*100,1)

            peaktimes = []
            for i in qrs_i:
                i = int(i)
                time = (i/fs) *1000
                peaktimes.append(time)

            nn_intervals = np.diff(peaktimes)
            IBI = round(np.mean(nn_intervals))

            ekg_data = {
                "Average Heart Rate": heart_rate,
                "Heart Rate Standard Deviation": hr_std_dev,
                "Interbeat Interval": IBI,
                "SDNN": SDNN,
                "SDSD": SDSD,
                "RMSSD": RMSSD,
                "NN50": nn50,
                "NN20": nn20,
                "pNN50": pNN50,
                "pNN20": pNN20,
                "LF/HF Ratio": low_high_freq_ratio
            }

            return ekg_data
    
    def get_rec_time(self, f) :
        rt = f.read(8).decode('utf-8')
        return rt
        
    def write_edf(self, filepath, equipment = None, rec_date = None):
        signal_labels = self.data.columns
        eeg_data = self.data.values.T
        #edf_filename = self._filename[:-4] + ".edf"
        edf_filename = filepath + ".edf"

        def signal_info(num):
            info = {}
            info['label'] = signal_labels[num]
            info['dimension'] ='uV'
            info['sample_rate'] = self.sampling_rate
            info['physical_max'] = 32767.0
            info['physical_min'] = -32768.0
            info['digital_max'] = 32767
            info['digital_min'] = -32768
            info['prefilter'] = 'X'
            info['transducer'] = 'X'
            return info


        fileHeader = {
            "technician":"n/a",
            "recording_additional":"n/a",
            "patientname":"n/a",
            "patient_additional":"n/a",
            "patientcode":"n/a",
            "equipment": equipment,
            "admincode":"n/a",
            "gender":"n/a",
            "startdate":rec_date,
            "birthdate":datetime.date(2000,1,1),
        }


        with pyedflib.EdfWriter(edf_filename, eeg_data.shape[0], file_type = 0 ) as f:
            f.setHeader(fileHeader)
            for i in range(len(signal_labels)): #sets signal header information for every channel in the EEG.
                f.setSignalHeader(i, signal_info(i))
            f.writeSamples(eeg_data, digital = False)

#             print(f'EDF Filepath: {edf_filename}')

    def write_csv(self):
        csv_filename = self._filename.split(".")[0] + ".csv"
        self.data.to_csv(csv_filename, index = False)
#         print(f'CSV Filepath: {csv_filename}')

    def write_json(self):
        if ((self.header['PID'] == False) or ('EKG' not in self.data.columns)):
            raise Exception(f'Insufficient information for JSON file. EEG file does not contain EKG signal, or field for PID. Use Deymed or EDF file format.')
        else:
            fs = self.sampling_rate
            qrs_i = Detectors(fs).pan_tompkins_detector(self.data['EKG'].values)
            hrv_measure = hrv.HRV(fs)
            heart_rates = hrv_measure.HR(qrs_i)
            heart_rate = round(np.mean(heart_rates)/60,1)

            output = {
                "metadata": self.header['PID'],
                "header": self.header,
                "heart_rate(Hz)": heart_rate ,
                "data": self.data.to_dict(orient = 'list')
            }
            json_file = self._filename[:-4] + ".json"
            json_object = json.dumps(output)
            with open(json_file, 'w') as outfile:
                outfile.write(json_object)
#             print(f'JSON Filepath: {json_file}')

    def bandpass(self,fl = 4, fh = 17):

        channels = ['Fz', 'Cz', 'Pz', 'Fp1', 'Fp2', 'F3', 'F4', 'F7','F8', 'C3', 'C4', 'T3', 'T4', 'P3', 'P4', 'T5', 'T6', 'O1', 'O2', 'EKG']

        data = self.data[channels].values.T
        EKG = self.data['EKG'].values
        fs = self.sampling_rate

        bandpass_window = [fl,fh]
        b,a = signal.cheby1(2, 0.5, bandpass_window, btype = 'bandpass', fs = fs) #butterworth filter outputting b,a - numerator and denominator polynomials of the IIR filter
        filt_data = signal.filtfilt(b,a,data) #applies a  linear digital filter backward and forward at least once. Returns an a filtered output with the same length as the input.

        self.data = pd.DataFrame(filt_data.T, columns = channels)
        self.data['EKG'] = pd.Series(EKG, index = self.data.index) # EKG should be processed apart from the EEG, morphology of the ekg should be preserved for classification.

        return self.data


    def slice(self, new_filename, interval, new_time=None):
        filename = self._filename
        extension = filename.split(".")[-1].lower()
        if 'dat' not in extension:
            raise NameError('Method only supported for Deymed EEG files ending in extension (*.dat).')
        else:
                filename = filename.strip(" '' ").strip(" ""  ") #removes quotation marks from filepath input,
                file = list(Path(filename).parts) #break filepath into its components
                file[-1] = new_filename #new filename sans names
                new_filename = str(pathlib.Path(*file)) #put it all together to form a string that will describe the new filepath
#                 print("\n" + new_filename)

                rec_time = self.header['recording time'] #time of EEG recording
                sampling_rate = self.header["sampling rate"] #sampling rate
                signals = self.__data

                with open(filename, "rb") as f:
                    header = f.read(512)

                    if new_time == None:
                        pass
                    elif new_time != None:
#                         print(type(rec_time))
#                         print(type(new_time))
                        header = header.replace(rec_time.encode('utf-8'), bytes(new_time, 'utf-8'))

                with open(new_filename, "wb") as binary_file: #open new filename in write binary mode; copy of Deymed file.
                    binary_file.write(header)
                    binary_file.seek(512,0)



                    if len(interval) > 2 or len(interval) == 1:
                        raise NameError('The "interval" parameter should only hold 2 integer elements.')

                    def str2int(t):
                        time_info = time.strptime(t, "%M:%S")
                        return (time_info.tm_min * 60) + (time_info.tm_sec)

                    interval = [seconds for seconds in map(str2int, interval)]

                    epoch_start, epoch_end = np.asarray(interval)*sampling_rate+2 #calculate epoch start/end index position. / adjust for Persyst 2 second cut off.

                    if epoch_start > epoch_end:
                        epoch_start,epoch_end = epoch_end, epoch_start

                    epoch_data = signals[:, epoch_start:epoch_end].flatten(order = 'F') # EEG segment
                    eeg_data = epoch_data.astype(np.int16)
                    binary_file.write(eeg_data) #write EEG segments in the new Deymed file.




    def censor(self,subject=1,eeg=1):
        filename = self._filename
        extension = filename.split(".")[-1].lower()
        if 'dat' not in extension:
            raise NameError('Method only supported for Deymed EEG files ending in extension (*.dat).')
        else:
            filename = filename.strip(" '' ").strip(" ""  ") #removes quotation marks from filepath input,
            file = list(Path(filename).parts) #break filepath into its components
            file[-1] = f'Subject {subject} EEG {eeg}.dat' #new filename sans names
            new_filename = str(pathlib.Path(*file)) #put it all together to form a string that will describe the new filepath

#             print("")
#             print(new_filename)

            with open(filename, "rb") as f:
                    header = f.read(512)

            header = bytearray(header)

            count = 0
            for char in range(16):
                header[12+count] = ord(" ")
                count += 1

            count = 0
            for char in range(12):
                header[28+count] = ord(" ")
                count += 1

            header = bytes(header)

            signals = self.__data.flatten(order= 'F')

            with open(new_filename, "wb") as binary_file: #open new filename in write binary mode; copy of Deymed file.
                binary_file.write(header)
                binary_file.seek(512,0)
                binary_file.write(signals.astype(np.int16))





    def notch(self, freq = 60):#attenuated external electrical noise. ( Can be set to 60 Hz for US, 50 Hz for Australia patients)
        data = self.data.values.T
        labels = self.data.columns

        fs = self.sampling_rate

        q = 2.0 #Q-factor
        b,a = signal.iirnotch(freq, q, fs) #applies band-stop filter with a narrow bandwidth (high quality factor). Reject narrow frequency band and leaves the rest of the spectrum unchanged. Returns the numerator (b) and denominator(a) polynomials of the IIR filter.

        filt_data = signal.filtfilt(b,a,data) #applies a  linear digital filter backward and forward at least once. Returns an a filtered output with the same length as the input.

        self.data = pd.DataFrame(filt_data.T, columns = labels)

        return self.data


    def smooth(self):
        data = self.data.values.T
        fs = self.sampling_rate

        #inner function will applied to all signals in the dataframe.
        def smoothing(signal, fs = fs):#reduces lead wandering.
            smoothed_signal = []
            s0, s2 = 0, 2*fs # sliding window -- 2 second interval segment

            while len(smoothed_signal) < len(signal):
                smoothed_signal.extend(signal[s0:s2] - np.mean(signal[s0:s2]) )#subtract mean from signal segment
                s0 += 2*fs
                s2 += 2*fs

            return smoothed_signal
        self.data = self.data.apply(smoothing, axis = 0)

        return self.data





    def get_raw(self):
        df = self.data

        channels = ['Fz', 'Cz', 'Pz', 'Fp1', 'Fp2', 'F3', 'F4', 'F7','F8', 'C3', 'C4', 'T3', 'T4', 'P3', 'P4', 'T5', 'T6', 'O1', 'O2', 'A1', 'A2', 'EKG']

        if ('A1' not in df.columns) or ('A2' not in df.columns):
           buffer =  np.zeros(df.shape[0])
           df['A1'] = buffer
           df['A2'] = buffer
        if('EKG' not in df.columns):
            buffer =  np.zeros(df.shape[0])
            df['EKG'] = buffer

        df = df[channels]
        df = df.rename(columns = {'EKG':'ecg'})

        df = df/10**6

        info = mne.create_info(ch_names = df.columns.to_list(), sfreq = self.sampling_rate)
        raw = mne.io.RawArray(data = df.values.T, info = info, verbose=True)

        ch_type = {}

        for i in df.columns:
            if (i == 'A1') or (i == 'A2'):
                ch_type[i] = 'misc'
            elif i != 'ecg':
                ch_type[i] = 'eeg'
            else:
                ch_type[i] = 'ecg'

        raw = raw.set_channel_types(ch_type)
        raw = raw.set_eeg_reference(ref_channels=['A1', 'A2'])

        return raw






import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from ecgdetectors import Detectors




def hrv_calculator(eeg, filepath):
    #eeg is the EEG data structure in cerebro
    filepath = Path(filepath)
    hrv = eeg.ekg_data() # contains dictionary where heart rate and other hrv measures are stored.


    hr_avg = str(hrv['Average Heart Rate'])
    hr_std_dev = str(hrv['Heart Rate Standard Deviation'])

    if float(hr_std_dev) >= 0.4*(float(hr_avg)): # set threshold for hrv measure rejection
        print("Heart Rate measures could not be determined due to limited clean data.")
    else:
        print(f'Patient Average Heart Rate (Mean ± Standard Deviation BPM): {hr_avg} ± {hr_std_dev}' )
        print("***********************************************************")

    xl = "Heart Rate Variability Records.xlsx" #set filename of excel where hrv data will be stored.
    rec = filepath.parent/ xl # full filepath as a pathlib object

    recording_date = eeg.header['recording date']


    if rec.is_file(): #check if excel file was already generated, if so it will be updated to include new data.
        existing_table = pd.read_excel(rec, index_col = 0)
        if filepath.name in existing_table['file'].values: #if file was already analyzed, the user will be notified
            print(f'\n{filepath.name} was already analyzed')
        else:
            hrv_rec = pd.DataFrame.from_dict(hrv, orient='index').T #create dataframe from hrv dictionary.
            hrv_rec['rec_date'] = eeg.header['recording date'] # add column holding date of recording in datetime format.
            hrv_rec['file'] = filepath.name # add a column to keep track of the filename being analyzed.
            hrv_rec['signed on'] = datetime.datetime.now() #mark the datetime the eeg file was analyzed.
            hrv_rec = hrv_rec.set_index('rec_date')

            if type(existing_table.index[-1]) == str: #fixes an error that occurs when pandas dataframe doesn't return an index in datetime format.
                existing_table['datetime'] = pd.to_datetime(existing_table.index)
                existing_table = existing_table.set_index('datetime')

            existing_table.append(hrv_rec).sort_index().to_excel(rec) #sort the data by recording date and save in an excel file.
            print(f'\nHRV Data saved: {rec}')
    else:
        hrv_rec = pd.DataFrame.from_dict(hrv, orient='index').T
        hrv_rec['rec_date'] = recording_date
        hrv_rec['file'] = filepath.name
        hrv_rec['signed on'] = datetime.datetime.now()
        hrv_rec = hrv_rec.set_index('rec_date')
        hrv_rec.to_excel(rec)
        print(f'\nHRV Data saved: {rec}\n')



def pan_peaks(self) :
        if "EKG" not in self.data.columns:
            raise Exception(f'File does not contain channel for electrocardiogram (EKG) data.')
        else:
            ekg = self.data['EKG'].values
            fs = self.sampling_rate

            detectors = Detectors(fs)

            qrs_i = detectors.pan_tompkins_detector(ekg)
            
        return qrs_i



def ekg_data(self):
    if "EKG" not in self.data.columns:
        raise Exception(f'File does not contain channel for electrocardiogram (EKG) data.')
    else:
        ekg = self.data['EKG'].values
        fs = self.sampling_rate

        detectors = Detectors(fs)

        qrs_i = detectors.pan_tompkins_detector(ekg)
#             print("qrs_i: ")
#             print(qrs_i)
        hrv_measure = hrv.HRV(fs) #

        heart_rates = hrv_measure.HR(qrs_i) # calculates and stores instantaneous heart rates in an array

        heart_rate = round(np.mean(heart_rates),1) #average heart rate

        hr_std_dev = round(np.std(heart_rates),1) #standard deviation of heart rates

        RMSSD = round(hrv_measure.RMSSD(qrs_i),1)
        SDNN = round(hrv_measure.SDNN(qrs_i),1)
        SDSD = round(hrv_measure.SDSD(qrs_i),1)
        nn50 = hrv_measure.NN50(qrs_i)
        nn20 = hrv_measure.NN20(qrs_i)
        pNN50 = round(hrv_measure.pNN50(qrs_i)*100,1)
        pNN20 = round(hrv_measure.pNN20(qrs_i)*100,1)
        low_high_freq_ratio = round(hrv_measure.fAnalysis(qrs_i)*100,1)

        peaktimes = []
        for i in qrs_i:
            i = int(i)
            time = (i/fs) *1000
            peaktimes.append(time)

        nn_intervals = np.diff(peaktimes)
        IBI = round(np.mean(nn_intervals))

        ekg_data = {
            "Average Heart Rate": heart_rate,
            "Heart Rate Standard Deviation": hr_std_dev,
            "Interbeat Interval": IBI,
            "SDNN": SDNN,
            "SDSD": SDSD,
            "RMSSD": RMSSD,
            "NN50": nn50,
            "NN20": nn20,
            "pNN50": pNN50,
            "pNN20": pNN20,
            "LF/HF Ratio": low_high_freq_ratio
        }

        return ekg_data