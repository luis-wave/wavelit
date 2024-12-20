


def get_test_eeg(file_type="edf", index="0"):
    try: 
        if not isinstance(index, str): index = str(index)
        
        
        eeg_file_dict = {
            "edf": {
                "0": "mywavelab/testing/eegs/eeg-5860.edf",
                "1": "mywavelab/testing/eegs/eeg-6086.edf",
                "2": "mywavelab/testing/eegs/EEG-1f55530a-bbac-426f-b3ba-5205a6237064-UC.edf",
                "3": "mywavelab/testing/eegs/EEG-5d8c1465-0325-481c-a126-a7c7b8455af6-UUC.edf"
            },

            "dat": {
                "0": "mywavelab/testing/eegs/eeg-2023-02-13.Dat",
                "1": "mywavelab/testing/eegs/EEG-403bc671-f335-440f-9214-0f8f2ac5a7d7.Dat",
                "2": "mywavelab/testing/eegs/EEG-34a159a1-7b96-483f-91f7-d379a0718087.dat",
                "3": "mywavelab/testing/eegs/EEG-e01d2498-ca03-4b18-9111-c9c81640f908-BHR.dat",
            }
        }

        return eeg_file_dict[file_type][index]

    except:
        print("IN file_testing.py's get_test_eeg(), THE PARAMS FAILED... USING DEFAULT EEG.")
        
        return eeg_file_dict["edf"]["0"]
    