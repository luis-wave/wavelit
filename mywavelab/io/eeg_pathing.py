
from pathlib import Path






def get_clean_paths(path_to_clean=""):
    """
    Normalizes a string path that could have bad characters from input.
    """

    # Strip trailing single/double quotes and curly braces
    path_to_clean = path_to_clean.replace("'", "").replace('"', "").replace("{", "").replace("}", "")

    # Create a Path object and normalize the path
    normalized_path = Path(path_to_clean).resolve()

    return str(normalized_path), normalized_path
