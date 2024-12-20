
import numpy as np

from ecgdetectors import Detectors
import hrv



def calc_ecg_stats(ecg=None, fs=None, store=True):
    try: 
        detectors = Detectors(fs)

        qrs_i = detectors.pan_tompkins_detector(ecg)

        hrv_measure = hrv.HRV(fs) #

        heart_rates = hrv_measure.HR(qrs_i) # calculates and stores instantaneous heart rates in an array

        heart_rate = round(np.mean(heart_rates),1) #average heart rate

        hr_std_dev = round(np.std(heart_rates),1) #standard deviation of heart rates

        reject_hrv_dict = reject_hrv(heart_rate, hr_std_dev)

        if store:
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

            ecg_data = {
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
                "LF/HF Ratio": low_high_freq_ratio,
            }

            ecg_data.update(reject_hrv_dict)

        else:
            ecg_data = {
                "Average Heart Rate": heart_rate,
                "Heart Rate Standard Deviation": hr_std_dev,
            }

            ecg_data.update(reject_hrv_dict)
            
        return ecg_data
        
    except Exception as e:
        print("MISSING OR IMPROPER ECG SETUP IN EEG FILE:")
        print(str(e))
        
        ecg_data = {
                "Average Heart Rate": None,
                "Heart Rate Standard Deviation": None,
            }
        
        return ecg_data
    

def reject_hrv(avg_hr, avg_sd):
    """
    Threshold determined by Alex Ring and Luis Camargo. If the standard deviation is
    greater than or equal to 40% of the average heart rate, then the average heart rate
    is not reliable for determining patient HRV measures.
    """
    
    reject = False
    avg_sd = float(avg_sd)

    # Set threshold for HRV measure rejection
    threshold = 0.4*(float(avg_hr))
    threshold_difference = round(threshold - avg_sd, 5)
    percent_of_threshold = round((avg_sd / threshold) * 100, 5)

    if avg_sd >= threshold: reject = True

    return {
        "Reject": reject, 
        "Threshold Difference": threshold_difference,
        "Percentage of Threshold": percent_of_threshold,
    }