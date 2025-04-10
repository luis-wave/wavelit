import streamlit as st
import plotly.graph_objects as go
import numpy as np

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots

# Function to plot power spectrum
def plot_power_spectrum(frequency, power, protocol_freq=None, confidence_interval=None):
    """
    Generates an interactive Plotly line graph of the power spectrum.

    Parameters:
    - frequency: array-like, X-axis values (frequency in Hz).
    - power: array-like, Y-axis values (power spectrum).
    - protocol_freq: float, frequency in Hz where a vertical dashed line is drawn.
    - confidence_interval: float, confidence range (+/-) around protocol_freq.

    Returns:
    - Plotly figure.
    """

    fig = go.Figure()

    if protocol_freq is not None:
        protocol_freq = round(protocol_freq, 2)
    if confidence_interval is not None:
        confidence_interval = round(confidence_interval, 2)

    frequency = np.array(frequency)
    power = np.mean(power, axis=0)

    min_freq = 4.0
    max_freq = 20.0
    mask = (frequency >= min_freq) & (frequency <= max_freq)

    # Apply the mask to filter frequencies and corresponding power values
    frequency = frequency[mask]
    power = power[mask]

    # Plot power spectrum with dark grey line
    fig.add_trace(go.Scatter(
        x=frequency,
        y=power,
        mode='lines',
        name='Posterior PSD',
        line=dict(color='rgb(80, 80, 80)', width=2),  # Dark Grey
        showlegend=False

    ))

    # Add vertical dashed line for protocol frequency
    if protocol_freq is not None:
        fig.add_trace(go.Scatter(
            x=[protocol_freq, protocol_freq],
            y=[min(power), max(power)],
            mode='lines',
            name=f'Protocol: {protocol_freq} Hz',
            line=dict(dash='dash', color='blue', width=2),
            showlegend=False
        ))

        # Add shaded confidence interval
        if confidence_interval is not None:
            lower_bound = protocol_freq - confidence_interval
            upper_bound = protocol_freq + confidence_interval

            fig.add_trace(go.Scatter(
                x=[lower_bound, upper_bound, upper_bound, lower_bound],
                y=[min(power), min(power), max(power), max(power)],
                fill='toself',
                fillcolor='rgba(0, 150, 255, 0.2)',  # Light blue shade
                line=dict(color='rgba(0,0,255,0)'),
                name=f'Protocol: {protocol_freq} ±{confidence_interval} Hz'
            ))

            # Add annotation for confidence interval
            fig.add_annotation(
                x=protocol_freq,
                y=min(power),
                text=f"Protocol: {protocol_freq} ±{confidence_interval} Hz",
                showarrow=False,
                font=dict(size=15, color='rgb(80, 80, 80)')
            )

    # Layout settings
    fig.update_layout(
        title="NGBoost Peak Protocol Generator",
        xaxis_title="Frequency (Hz)",
        yaxis_title="Amplitude (µV)",
        template="plotly_white"
    )

    return st.plotly_chart(fig, use_container_width=True)


def plot_burst_analysis(xf, f_array, magnitude_spectra, burst_protocol=None, burst=None):
    """
    Create a simplified plot showing magnitude spectra and bursts.

    Parameters:
    -----------
    xf : pandas DataFrame
        DataFrame containing columns 'avg_frequency_hz', 'avg_amplitude', and 'duration_seconds'
    f_array : array-like
        Frequency array for the magnitude spectra
    magnitude_spectra : array-like
        Magnitude spectra values corresponding to frequencies in f
    burst_protocol : float, optional
        Protocol burst frequency to mark with vertical line (can be None)
    burst : float, optional
        Burst quantile protocol frequency to mark with vertical line (can be None)

    Returns:
    --------
    None : Displays the chart directly in Streamlit
    """
    magnitude_array = np.array(magnitude_spectra)

    # Define the 8-13 Hz mask for maximum amplitude calculation
    burst_mask = (xf['avg_frequency_hz'] >= 8) & (xf['avg_frequency_hz'] <= 13)
    spectra_mask = (f_array >= 8) & (f_array <= 13)

    # Get max values in the 8-13 Hz range
    max_burst_amp = xf.loc[burst_mask, 'avg_amplitude'].max() if any(burst_mask) else 0
    max_spectra_amp = np.max(magnitude_array[spectra_mask]) if any(spectra_mask) else 0

    # Set Y max accordingly (plus a little margin)
    ymax = max(max_burst_amp, max_spectra_amp) * 1.1

    # Create figure
    fig = go.Figure()

    # Add magnitude spectra line
    fig.add_trace(
        go.Scatter(
            x=f_array,
            y=magnitude_array,
            mode='lines',
            line=dict(color='black', width=2),
            name='Magnitude Spectra'
        )
    )

    # Add scatter plot for burst data with size representing duration
    size_values = xf['duration_seconds'] * 100  # Scale for better visibility
    fig.add_trace(
        go.Scatter(
            x=xf['avg_frequency_hz'],
            y=xf['avg_amplitude'],
            mode='markers',
            marker=dict(
                size=size_values,
                sizemode='area',
                sizemin=5,
                sizeref=2.*max(size_values)/(30.**2),
                color='blue',
                opacity=0.2
            ),
            name='Bursts',
            hovertemplate='<b>Frequency:</b> %{x:.2f} Hz<br><b>Amplitude:</b> %{y:.2f}<br><b>Duration:</b> %{text:.2f} s',
            text=xf['duration_seconds']
        )
    )

    # Create custom legend entries for vertical lines and alpha band
    legendgroups = []

    # Add alpha band shaded region (8-13 Hz) with legend entry
    fig.add_vrect(
        x0=8, x1=13,
        fillcolor="gray", opacity=0.1,
        layer="below", line_width=0,
        name="Alpha Band (8-13 Hz)"
    )
    legendgroups.append("Alpha Band (8-13 Hz)")

    # Add vertical lines for protocol markers with frequency values in legend
    if burst_protocol is not None:
        protocol_name = f"NGBoost Burst Protocol: {burst_protocol:.2f} Hz"
        fig.add_trace(
            go.Scatter(
                x=[burst_protocol, burst_protocol],
                y=[0, ymax],
                mode='lines',
                line=dict(color='red', dash='dash', width=1.5),
                name=protocol_name,
                showlegend=True
            )
        )
        legendgroups.append(protocol_name)

    if burst is not None:
        quantile_name = f"Burst Protocol: {burst:.2f} Hz"
        fig.add_trace(
            go.Scatter(
                x=[burst, burst],
                y=[0, ymax],
                mode='lines',
                line=dict(color='purple', dash='dot', width=1.5),
                name=quantile_name,
                showlegend=True
            )
        )
        legendgroups.append(quantile_name)

    # Update layout
    fig.update_layout(
        title='NGBoost Burst Protocol Generator',
        xaxis=dict(
            title='Frequency (Hz)',
            range=[4, 20],
            gridcolor='lightgrey'
        ),
        yaxis=dict(
            title='Amplitude',
            range=[0, ymax],
            gridcolor='lightgrey'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='lightgrey',
            borderwidth=1
        ),
        plot_bgcolor='white'
    )

    # Add annotations
    if burst_protocol is not None:
        fig.add_annotation(
            x=burst_protocol,
            y=ymax * 0.95,
            text=f"{burst_protocol:.2f} Hz",
            showarrow=False,
            font=dict(color='red', size=10),
            bgcolor="rgba(255,255,255,0.8)"
        )

    if burst is not None:
        fig.add_annotation(
            x=burst,
            y=ymax * 0.85,
            text=f"{burst:.2f} Hz",
            showarrow=False,
            font=dict(color='purple', size=10),
            bgcolor="rgba(255,255,255,0.8)"
        )

    return st.plotly_chart(fig, use_container_width=True)