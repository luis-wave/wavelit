from pathlib import Path

import mywaveanalytics
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from mywaveanalytics.pipelines import ngboost_protocol_pipeline


def plot_psd_against_freqs(file, psd_avg, freqs, protocol, std_dev):
    psd = np.array(psd_avg)
    psd = (psd * 10**12) ** 0.5
    data = pd.DataFrame({"Frequency": freqs, "Posterior Magnitude Spectra": psd})
    filtered_data = data[(data["Frequency"] >= 3) & (data["Frequency"] <= 20)]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=filtered_data["Frequency"],
            y=filtered_data["Posterior Magnitude Spectra"],
            mode="lines",
            name="Posterior Magnitude Spectra",
        )
    )
    fig.add_vline(
        x=protocol,
        line=dict(color="red", dash="dash"),
        annotation_text=f"Protocol: {round(protocol,1)} Hz",
        annotation_position="top left",
    )
    fig.add_vrect(
        x0=protocol - std_dev,
        x1=protocol + std_dev,
        fillcolor="red",
        opacity=0.3,
        line_width=0,
        annotation_text=f"Confidence Interval: ±{round(std_dev,2)} Hz",
        annotation_position="bottom left",
    )
    fig.update_layout(
        title=f"{file}",
        xaxis_title="Frequency (Hz)",
        yaxis_title="Magnitude Spectra (µV)",
        yaxis=dict(range=[0, max(filtered_data["Posterior Magnitude Spectra"]) * 1.1]),
        legend_title="Legend",
        template="plotly_white",
    )
    st.plotly_chart(fig)


def get_ngboost_protocol(path):
    try:
        eeg_type = (
            10 if ".edf" in path.lower() else 0 if ".dat" in path.lower() else None
        )
        if ".401" in path.lower():
            eeg_type = 6
        # if eeg_type is None:
        #     return None, None, None, None
        # print(eeg_type)
        # print(path)
        mw_object = mywaveanalytics.MyWaveAnalytics(path, None, None, eeg_type)
        pipeline = ngboost_protocol_pipeline.NGBoostProtocolPipeline(mw_object)
        pipeline.run()
        analysis = pipeline.analysis_json
        return (
            float(analysis["ngb_protocol"]),
            float(analysis["ngb_std_dev"]),
            list(analysis["psd_avg"]),
            list(analysis["freqs"]),
        )
    except Exception as e:
        f"{path} failed to process: {e}"


def load_data(directory):
    valid_extensions = ["edf", "dat", "401"]
    files = [
        str(f)
        for f in Path(directory).glob("*")
        if any(f.name.lower().endswith(ext) for ext in valid_extensions)
    ]
    results = []
    total_files = len(files)
    progress_bar = st.progress(0)
    st.caption(f"Processing {total_files} files...")
    for i, file in enumerate(files):
        try:
            filename = Path(file).name
            protocol, std_dev, psd_avg, freqs = get_ngboost_protocol(file)
            results.append(
                {
                    "file": filename,
                    "protocol": protocol,
                    "confidence_interval": std_dev,
                    "psd_avg": psd_avg,
                    "freqs": freqs,
                }
            )
        except Exception as e:
            print(f"Unable to generate protocol for file : {filename}")
        progress_bar.progress((i + 1) / total_files)
    df = pd.DataFrame(results)

    return df.sort_values(by="file").reset_index(drop=True)


st.title("NGBoost Protocol Recommendations")
directory = st.text_input("Enter the directory path:", "cases")

if st.button("Load Data", key="load_data"):
    if directory:
        data = load_data(directory)
        if not data.empty:
            st.write(data[["file", "protocol", "confidence_interval"]])
            st.bar_chart(data.set_index("file")["protocol"])
            for idx, row in data.iterrows():
                try:
                    plot_psd_against_freqs(
                        row["file"],
                        row["psd_avg"],
                        row["freqs"],
                        row["protocol"],
                        row["confidence_interval"],
                    )
                except Exception as e:
                    print(
                        f"{row['file']}: failed to generate graph for the following reason. {e}, {row['psd_avg']}"
                    )
        else:
            st.error(
                "No data found in the specified directory or there was an error processing the data."
            )
    else:
        st.error("Please enter a valid directory path.")
