from mywaveanalytics.libraries import (database, eeg_artifact_removal,
                                       eeg_computational_library, filters,
                                       mywaveanalytics, references)
from mywaveanalytics.pipelines import ngboost_protocol_pipeline

from pipeline import PersistPipeline

path = "test_eegs/typical_eeg.dat"

if path.lower().endswith(".dat"):
    eeg_type = 0
else:
    eeg_type = 10

mw_object = mywaveanalytics.MyWaveAnalytics(path, None, None, eeg_type)

pipeline = ngboost_protocol_pipeline(mw_object)

print(pipeline.analysis_json)
