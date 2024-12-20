from io import BytesIO
import mne
import numpy as np
import pandas as pd
import datetime

from mywavelab.parsers.parser import Parser
from ..utils import params



class Deymed(Parser):
    def __init__(self, file_str):
        super().__init__(file_str)

        self.file_str = file_str
        self.data = None
        self.initial_ch_names = None
        self.initial_ref = None
        self.ch_names = None
        self.initial_ref = None

        self.parse_eeg()


    def parse_eeg(self):
        with open(self.file_str, "rb") as reader:
            iobytes = BytesIO(reader.read())
        f = iobytes

        subject_info = {}
        # Header
        subject_info["id"] = f.read(12).decode("utf-8")
        subject_info["last_name"] = (
            f.read(16).decode("latin-1").strip().title().split("\x00", 1)[0]
        )
        subject_info["last_name"] = "".join(
            [i for i in subject_info["last_name"] if not i.isdigit()]
        )

        subject_info["first_name"] = (
            f.read(12).decode("latin-1").strip().title().split("\x00", 1)[0]
        )
        subject_info["first_name"] = "".join(
            [i for i in subject_info["first_name"] if not i.isdigit()]
        )

        recording_date = f.read(12).decode("utf-8").strip().split("\x00", 1)[0]

        """
        grabbed from EEG lab scripts.
        """
        if len(recording_date.split(".")[-1]) > 4 and ("." in recording_date):
            # will check to see if any extra characters are found in the recording date. (i.e '2017ro')
            test_date_parts = recording_date.split(
                "."
            )  # splits string into an array, string separated by "."
            test_date_parts[-1] = test_date_parts[-1][:4]

            # the extra characters are found in the year field. The year is always 4 digits
            # we only need the first 4 characters.
            recording_date = ".".join(test_date_parts)  # join by "."

        elif len(recording_date.split("/")[-1]) > 4 and ("/" in recording_date):
            test_date_parts = recording_date.split(
                "/"
            )  # splits string into an array, string separated by "."
            test_date_parts[-1] = test_date_parts[-1][:4]
            # the extra characters are found in the year field.
            # The year is always 4 digits, we only need the first 4 characters.
            recording_date = "/".join(test_date_parts)  # join by "/"

        elif len(recording_date.split("-")[-1]) > 4 and ("-" in recording_date):

            test_date_parts = recording_date.split(
                "-"
            )  # splits string into an array, string separated by "."
            test_date_parts[-1] = test_date_parts[-1][:4]
            # the extra characters are found in the year field. The year is always 4 digits
            # we only need the first 4 characters.
            recording_date = "-".join(test_date_parts)  # join by "-"

        rec_time = f.read(8).decode("utf-8")
        date_time = recording_date + " " + rec_time
        try:
            d_t: datetime = Parser.make_date_obj(date_time)
        except ValueError:
            print("Datetime parsing failed")

        sampling_rate = ord(f.read(1))

        f.seek(1, 1)  # skipping sensitivity byte, it's always 4 in Deymed.

        if (
            sampling_rate == 0
        ):  # if sampling rate is 0, need to go back and ready two bytes as an integer, real sampling frequnecy (fs) > 256 Hz.
            f.seek(-2, 1)
            sampling_rate = int.from_bytes(f.read(2), "little")

        channels_count = ord(f.read(1))

        f.seek(1, 1)

        my_channels = range(channels_count)
        channels = []

        for _ in my_channels:
            string = f.read(6).decode("utf-8").replace("\x00", "").strip()
            channels.append(string)

        channels[21] = "ECG"  # using ECG instead of EKG to match edf file format

        if sampling_rate == 200:
            pass
        else:
            sampling_rate = 256

        ch_types = ["eeg"] * channels_count
        ch_types[19:21] = ["ecg"] * 2 # ch_types[21:23] = ["ecg"] * 2
        ch_types[21:] = ["misc"] * (channels_count - 21) # ch_types[23:] = ["misc"] * 3
        # ch_types[19:21] = ["misc"] * 2 # reference channels

        f.seek(512, 0)
        f = f.read()
        data = np.frombuffer(f, dtype=np.int16, count=-1)

        dat = data.size
        nRec = int(dat / channels_count)
        signals = np.reshape(data, (channels_count, nRec), order="F")
        signals = signals.astype("float64")
        signals[0:channels_count] = (
            signals[0:channels_count] / 4000000
        )  # sensitivity set to 4 and dividing by 1 million to reach microvolts

        # Counter measure for missing non EEG channels, if missing generate synthetic signal of 0s.
        df = pd.DataFrame(data=signals.T, columns=channels)

        # On synthesize signals for non-EEG channels.
        suppl_channels = ("ECG", "EKG2", "Oz", "Foto", "Info")
        buffer_df = pd.DataFrame(columns=suppl_channels)

        # Synthesize zero buffer signals for missing channels, reorder in Deymed format.
        total_df = df.align(buffer_df, fill_value=0)[0][
            list(params.CHANNEL_ORDER_DEYMED)
        ]

        signals = total_df.values.T
        channels = total_df.columns.to_list()
        info = mne.create_info(channels, sampling_rate, ch_types)

        info["subject_info"] = subject_info
        info["description"] = "Created from a Deymed .dat file"

        self.data = mne.io.RawArray(signals, info)
        # noinspection PyTypeChecker
        try:
            self.data.set_meas_date(d_t)
        except UnboundLocalError:
            print("Could not set a measurement time/date")

        # use average of mastoid channels as reference
        self.data.set_eeg_reference(ref_channels=["A1", "A2"])

        # try:
        #     self.data.load_data()
        #     ch_names = self.data.info["ch_names"]
        #     self.data.reorder_channels(Parser.order_channels(params.CHANNEL_ORDER_DEYMED, ch_names))
        #     self.ch_names = self.data.ch_names
        # except ValueError as e:
        #     print("Could not find all EEG channels")
        #     raise e

