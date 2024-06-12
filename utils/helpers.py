    """
    A collection of helper function that can be used across the system.
    """

def format_single(second):
    # Calculate minutes and seconds
    minutes, seconds = divmod(int(second), 60)
    return f"{minutes:02}:{seconds:02}"