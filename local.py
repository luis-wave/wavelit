from mywaveanalytics.libraries import (
    database,
    eeg_artifact_removal,
    eeg_computational_library,
    filters,
    references,
    mywaveanalytics,
)

from pipeline import PersistPipeline

path = "test_eegs/EEG-1e344494-8933-4bfd-9ffd-c2d276c44f89.dat"

if path.lower().endswith(".dat"):
    eeg_type = 0
else:
    eeg_type = 10

mw_object = mywaveanalytics.MyWaveAnalytics(path, None, None, eeg_type)

pipeline = PersistPipeline(mw_object)

print(pipeline.data)
