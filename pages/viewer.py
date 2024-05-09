import streamlit as st
import seaborn as sns
import plotly.graph_objects as go
from mywaveanalytics.libraries import references
from pipeline import bipolar_transverse_montage
import pandas as pd

# Streamlit app setup
st.set_page_config(page_title="EEG Visualization", layout="wide")

# Title
st.title("EEG Visualization Dashboard")

# Initialize onsets DataFrame in session state
if 'onsets' not in st.session_state:
    st.session_state['onsets'] = pd.DataFrame(columns=['onset'])

# Function to convert a MyWaveAnalytics object to a DataFrame with resampling
def mw_to_dataframe_resampled(mw_object, sample_rate=50):
    try:
        raw = mw_object.eeg
        raw = raw.resample(sample_rate)
        df = raw.to_data_frame()
        df['time'] = df.index / sample_rate
        return df
    except Exception as e:
        st.error(f"Failed to convert EEG data to DataFrame: {e}")
        return None

# Apply different references based on user selection
def apply_reference(mw_object, ref):
    ref_func = {
        "linked ears": None,
        "centroid": references.centroid,
        "bipolar transverse": bipolar_transverse_montage,
        "bipolar longitudinal": references.bipolar_longitudinal_montage,
        "temporal central parasagittal": references.temporal_central_parasagittal
    }.get(ref, None)

    if ref_func:
        return ref_func(mw_object.copy())
    else:
        return mw_object.copy()

# Plotly figure creation
def create_plotly_figure(df, channels, offset_value, colors):
    fig = go.Figure()
    channels = channels[::-1]

    for i, channel in enumerate(channels):
        offset = i * offset_value
        fig.add_trace(
            go.Scattergl(
                x=df['time'],
                y=df[channel] + offset,  # Apply vertical offset
                mode="lines",
                name=channel,
                line=dict(color=colors[i]),
            )
        )

    # Create custom y-axis tick labels and positions
    yticks = [i * offset_value for i in range(len(channels))]
    ytick_labels = channels

    filename = st.session_state.get('fname', 'EEG Visualization')

    fig.update_layout(
        title=filename,
        xaxis_title="Time",
        yaxis_title="EEG Channels",
        xaxis={"rangeslider": {"visible": True}, 'range': [0, 20]},
        yaxis={
            "tickvals": yticks,
            "ticktext": ytick_labels,
            "tickmode": "array",
            "range": [-100, max(yticks) + offset_value]
        },
        height=1200,  # Consistent height
    )
    return fig

# Function to assign ECG channel types if present
def assign_ecg_channel_type(raw, ecg_channels):
    existing_channels = raw.ch_names
    channel_types = {ch: 'ecg' for ch in ecg_channels if ch in existing_channels}
    raw.set_channel_types(channel_types)

# Function to filter EEG and ECG channels
def filter_eeg_ecg_channels(raw):
    picks = raw.pick_types(eeg=True, ecg=True).ch_names
    return picks

# Function to order channels
def order_channels(channels, ordered_list):
    ordered_channels = [ch for ch in ordered_list if ch in channels]
    remaining_channels = [ch for ch in channels if ch not in ordered_channels]
    return ordered_channels + remaining_channels

# Check if `mw_object` is available
if 'mw_object' in st.session_state and st.session_state.mw_object:
    mw_object = st.session_state.mw_object

    mw_object = mw_object.copy()

    # Reference selection
    ref = st.selectbox(
        "Choose EEG Reference",
        options=[
            "linked ears",
            "centroid",
            "bipolar transverse",
            "bipolar longitudinal",
            "temporal central parasagittal"
        ],
        index=0  # Default to 'linked ears'
    )

    # Apply the selected reference, but skip re-referencing if "linked ears" is selected
    if ref != "linked ears":
        mw_object.eeg = apply_reference(mw_object.eeg, ref)

    # Assign ECG channel type if present
    ecg_channels = ['ECG', 'ECG1', 'ECG2']
    assign_ecg_channel_type(mw_object.eeg, ecg_channels)

    # Extract only EEG and ECG channels
    channels = filter_eeg_ecg_channels(mw_object.eeg)

    # Define the specific ordering
    eeg_order = [
        'Fz', 'Cz', 'Pz', 'Fp1', 'Fp2', 'F3', 'F4',
        'F7', 'F8', 'C3', 'C4', 'T3', 'T4',
        'T5', 'T6', 'P3', 'P4', 'O1', 'O2'
    ]

    # Apply specific ordering only if not a bipolar montage or TCP
    if ref not in ["bipolar transverse", "bipolar longitudinal", "temporal central parasagittal"]:
        channels = order_channels(channels, eeg_order)

    # Channel multiselect widget
    selected_channels = st.multiselect(
        "Select EEG and ECG Channels to Visualize",
        channels,
        default=channels
    )

    # Offset value slider
    offset_value = st.slider(
        "Vertical Offset Between Channels",
        min_value=5, max_value=300, value=100, step=5
    )

    # Color palette
    flare_palette = sns.color_palette("flare", len(selected_channels))
    colors = [f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})" for r, g, b in flare_palette]

    # Create DataFrame from MyWaveAnalytics object
    df = mw_to_dataframe_resampled(mw_object, sample_rate=50)
    if df is not None:
        # Filter the DataFrame to include only selected channels
        missing_channels = [channel for channel in selected_channels if channel not in df.columns]
        if missing_channels:
            st.warning(f"Missing channels in the file: {missing_channels}")
            selected_channels = [channel for channel in selected_channels if channel in df.columns]

        # Generate the Plotly figure
        fig = create_plotly_figure(df, selected_channels, offset_value, colors)

        # Display the Plotly figure
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("No EEG data available. Please upload an EEG file on the main page.")
