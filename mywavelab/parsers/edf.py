import mne
import re
from collections import Counter

from mywavelab.parsers.parser import Parser
from ..utils import params



class Edf(Parser):
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
        self.data = mne.io.read_raw_edf(self.file_str, preload=True)
        self.data.info["description"] = "Created from an .edf file"
        self.initial_ch_names = self.data.ch_names

        print(self.initial_ch_names)

        for channel in self.initial_ch_names:
            if "ecg" in channel.lower() or "ekg" in channel.lower():
                self.data.set_channel_types({channel: "ecg"})
            elif "exg" in channel.lower():
                self.data.set_channel_types({channel: "ecg"})
                ch_parts = channel.split(" ")
                if len(ch_parts) > 1: 
                    ch_part = ch_parts[1].strip()
                    new_ch_name = 'ExG' + ch_part
                    self.data.rename_channels({channel: new_ch_name})
            elif "x1:s3" in channel.lower():
                self.data.set_channel_types({channel: "ecg"})
                self.data.rename_channels({channel: "ECG X1:S3"})
            elif (
                "oz" in channel.lower()
                or "foto" in channel.lower()
                or "info" in channel.lower()
                or "a" in channel.lower()
            ):
                self.data.set_channel_types({channel: "misc"})

        self.initial_ref = Edf.determine_reference(self.data.ch_names)
        self.data.rename_channels(Edf.loose_parse_channels)
        self.ch_names = self.data.ch_names

        self.set_ref(self.initial_ref)

        try:
            self.data.reorder_channels(Parser.order_channels(params.CHANNEL_ORDER_EDF, self.ch_names))
            self.ch_names = self.data.ch_names
        except Exception as e:
            print(f"\nERROR COMPARING {params.CHANNEL_ORDER_EDF} WITH {self.ch_names} WHEN REORDERING CHANNELS:")
            print(str(e))
        

    @classmethod
    def determine_reference(cls, ch_names):
        pattern = re.compile(r".*-(\w+)")
        refs = []
        for ch in ch_names:
            match = re.match(pattern, ch)
            if match:
                refs.append(match.group(1))

        if refs:
            c = Counter(refs)
            ref_channel = c.most_common(1)[0][0]
        else:
            return "LE"
        return ref_channel


    @classmethod
    def loose_parse_channels(cls, ch_name):
        if ch_name.upper() in ('ECG', 'EKG'):
            return 'ECG'
        pattern = re.compile(r"^ \W? (?:\w+\s)? \W? (\w+) \W? (?:.+)?$", re.VERBOSE)
        match = re.match(pattern, ch_name)
        if match:
            ch_name = match.group(1)
        for channel in params.CHANNEL_ORDER_EDF:
            if ch_name.lower() == channel.lower():
                return channel
        return ch_name
    

    def set_ref(self, ref):
        if ref == "LE":
            pass
        elif ref.lower() in tuple([ch.lower() for ch in params.CHANNEL_ORDER_EDF]) and ref not in self.data.ch_names:
            self.data = mne.add_reference_channels(self.data, [ref])

        if set(["A1", "A2"]).issubset(set(self.data.ch_names)):
            self.data.set_eeg_reference(ref_channels=['A1', 'A2'])