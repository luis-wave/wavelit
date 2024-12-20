"""


CHANNEL_ORDER_EDF -> Includes the order of all channels. 
                Channels need to just be excluded depending on the reference.
                This should work for LE, Cz, Avg, and Recorded.

CHANNEL_ORDER_DEYMED -> Includes the order of all channels. 
                    Channels need to just be excluded depending on the reference.
                    This should work for LE, Cz, Avg, and Recorded.
    
TCP_ANODES / TCP_CATHODES -> Channels and their order for Temporal-central-parasagittal montage.

BPT_ANODES / BPT_CATHODES -> Channels and their order for Bipolar-Transverse montage.
"""



CHANNEL_ORDER_EDF = (
    "Fz",
    "Cz",
    "Pz",
    "Fp1",
    "Fp2",
    "F3",
    "F4",
    "F7",
    "F8",
    "C3",
    "C4",
    "T3",
    "T4",
    "P3",
    "P4",
    "P7",
    "P8",
    "T5",
    "T6",
    "O1",
    "O2",
    "ECG",
    "EKG2",
    "X1",
    "ExG1",
    "ECG X1:S3",
    "1",
    "A1",
    "A2",
    "Oz",
    "Foto",
    "Info",
    "ACC21",
    "ACC22",
    "ACC23",
    "Counter",
    "TRIGGER",
)


CHANNEL_ORDER_DEYMED = (
    "Fz",
    "Cz",
    "Pz",
    "Fp1",
    "Fp2",
    "F3",
    "F4",
    "F7",
    "F8",
    "C3",
    "C4",
    "T3",
    "T4",
    "P3",
    "P4",
    "T5",
    "T6",
    "O1",
    "O2",
    "ECG",
    "EKG2",
    "A1",
    "A2",
    "Oz",
    "Foto",
    "Info",
)


TCP_ANODES = [
    "Fp1",
    "F7",
    "T3",
    "T5",
    "Fp2",
    "F8",
    "T4",
    "T6",
    "T3",
    "C3",
    "Cz",
    "C4",
    "Fp1",
    "F3",
    "C3",
    "P3",
    "Fp2",
    "F4",
    "C4",
    "P4",
]
TCP_CATHODES = [
    "F7",
    "T3",
    "T5",
    "O1",
    "F8",
    "T4",
    "T6",
    "O2",
    "C3",
    "Cz",
    "C4",
    "T4",
    "F3",
    "C3",
    "P3",
    "O1",
    "F4",
    "C4",
    "P4",
    "O2",
]


BPT_ANODES = [
    'F7',
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
    'O2'
]
BPT_CATHODES = [
    'Fp1',
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
    'T6'
]