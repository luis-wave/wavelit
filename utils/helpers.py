"""
A collection of helper function that can be used across the system.
"""

import numpy as np
import pytz
from datetime import datetime, date
import re



def format_func(value, tick_number):
    # convert second to minute and second, return as string 'mm:ss'
    mins, secs = divmod(int(value), 60)
    return f"{mins:02}:{secs:02}"


def format_single(second):
    # Calculate minutes, seconds, and milliseconds
    minutes, seconds = divmod(int(second), 60)
    milliseconds = int((second - int(second)) * 1000)
    return f"{minutes:02}:{seconds:02}.{milliseconds:03}"


# Function to assign ECG channel types if present
def assign_ecg_channel_type(raw, ecg_channels=["ECG", "ECG1", "ECG2"]):
    existing_channels = raw.ch_names
    channel_types = {ch: "ecg" for ch in ecg_channels if ch in existing_channels}
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


def grade_alpha(score, all_scores):
    """
    Assign a letter grade based on where the score ranks within all_scores using percentiles.

    Args:
    - score (float): The score for which you want to determine the grade.
    - all_scores (list of float): List of all scores to determine the percentiles.

    Returns:
    - grade (str): The letter grade.
    """

    A_threshold = np.percentile(all_scores, 99)
    B_threshold = np.percentile(all_scores, 95)
    C_threshold = np.percentile(all_scores, 80)
    D_threshold = np.percentile(all_scores, 60)
    E_threshold = np.percentile(all_scores, 40)

    if score >= A_threshold:
        grade = "A"
    elif score >= B_threshold:
        grade = "B"
    elif score >= C_threshold:
        grade = "C"
    elif score >= D_threshold:
        grade = "D"
    elif score >= E_threshold:
        grade = "E"
    else:
        grade = "F"

    return grade


def grade_bads(bad_count):
    """
    Assigns a grade based on the number of bad items.

    :param bad_count: (int) The number of bad items.
    :return: (str) The grade corresponding to the number of bad items.
    """
    if bad_count < 1:
        return "A"
    elif bad_count > 15:
        return "F"
    elif bad_count > 12:
        return "D"
    elif bad_count > 9:
        return "C"
    elif bad_count > 3:
        return "B"
    else:
        return "A"




def calculate_age(date_string: str) -> int:
    """
    Calculate age (in years) from date string
    Expected format: e.g. 'Tue May 09 2017'
    """
    birth_date = datetime.strptime(date_string, "%a %b %d %Y").date()

    # Get today's date
    today = date.today()

    # Calculate the preliminary age
    age = today.year - birth_date.year

    # Adjust if the birthday hasn't occurred yet this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age


def format_datetime(date_str):
    if not date_str:
        return "Not reviewed yet"
    try:
        # Convert the input ISO format string to a datetime object in UTC
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Define the Pacific Standard Time timezone
        pst = pytz.timezone('America/Los_Angeles')
        # Convert the datetime to PST
        dt_pst = dt.astimezone(pst)
        return dt_pst.strftime("%b %d, %Y at %I:%M %p %Z")
    except Exception as e:
        return f"Error parsing date: {e}"


def parse_recording_date(date_str):
    """
    Removes 'st', 'nd', 'rd', 'th' from the day and converts 'am'/'pm' to uppercase,
    then parses the cleaned string with strptime.
    """
    # 1. Remove 'st', 'nd', 'rd', 'th' from day
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

    # 2. Convert 'am'/'pm' to 'AM'/'PM'
    date_str = re.sub(r'\bam\b', 'AM', date_str)
    date_str = re.sub(r'\bpm\b', 'PM', date_str)

    # 3. Parse with the desired format
    return datetime.strptime(date_str, "%a, %B %d %Y, %I:%M:%S %p")
