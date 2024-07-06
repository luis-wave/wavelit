import numpy as np
import plotly.graph_objects as go
import streamlit as st


@st.cache_resource
def psd_peaks_3d(freqs, psd, epochs, alpha_scores):
    # Create a 3D plot
    fig = go.Figure()

    # Create a meshgrid for x and y
    X, Y = np.meshgrid(freqs, epochs)

    # Stack the Z values (PSD data)
    Z = np.vstack(psd)

    # Create the surface plot
    surface = go.Surface(
        x=X,
        y=Y,
        z=Z,
        surfacecolor=np.tile(alpha_scores, (len(freqs), 1)).T,
        colorscale="ice",
        cmin=0,
        cmax=np.max(alpha_scores),
    )

    fig.add_trace(surface)

    fig.update_layout(
        title="3D PSD Plot Across All Epochs",
        scene=dict(
            xaxis_title="Frequency (Hz)",
            yaxis_title="Epochs",
            zaxis_title="PSD (uV^2/Hz)",
            xaxis=dict(range=[2.2, 20]),
            zaxis=dict(range=[0, 100]),
        ),
        width=1200,
        height=1200,
    )

    return fig