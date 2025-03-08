import streamlit as st
import plotly.graph_objects as go
import numpy as np

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
        showlengend=False

    ))

    # Add vertical dashed line for protocol frequency
    if protocol_freq is not None:
        fig.add_trace(go.Scatter(
            x=[protocol_freq, protocol_freq],
            y=[min(power), max(power)],
            mode='lines',
            name=f'Protocol: {protocol_freq} Hz',
            line=dict(dash='dash', color='blue', width=2),
            showlengend=False
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
        title="NGBoost Protocol Generator",
        xaxis_title="Frequency (Hz)",
        yaxis_title="Power",
        template="plotly_white"
    )

    return st.plotly_chart(fig, use_container_width=True)
