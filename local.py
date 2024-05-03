from mywaveanalytics.libraries import (database, eeg_artifact_removal,
                                       eeg_computational_library, filters,
                                       mywaveanalytics, references)

from pipeline import PersistPipeline

path = "test_eegs/Camargo, Luis - 2021-11-24T23_40_52.140911Z.dat"

if path.lower().endswith(".dat"):
    eeg_type = 0
else:
    eeg_type = 10

mw_object = mywaveanalytics.MyWaveAnalytics(path, None, None, eeg_type)

pipeline = PersistPipeline(mw_object)

print(pipeline.data)
