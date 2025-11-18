from pathlib import Path
import re

import pandas as pd

"""
    exports the data frame to an excel document. Eventually I'd like to export different sheets all at different stages of cleaning.
"""
def export_to_excel(playlist_name: str, playlist_frame: pd.DataFrame) -> None:

    save_location = Path("/Users/intern/Documents/Miles/spotify_playlist_exporter/test_exports")
    
    files = [file.name for file in save_location.glob(f"{playlist_name}*.xlsx") if file.is_file]

    duplicate_found = False
    max = 1
    new_name = playlist_name # This line might be redundant, except for the fact that I'm instantiating the value as something useful

    for file_name in files:

        pattern = re.escape(playlist_name) + r"(\((\d+)\)){0,1}.xlsx$"
        match = re.search(pattern=pattern, string=file_name)

        if match is not None:

            duplicate_found = True

            if match.group(2) is not None:

                if int(match.group(2)) >= max:

                    max = int(match.group(2)) + 1

    if duplicate_found:
        new_name = playlist_name + f"({max})"

    playlist_frame.to_excel(f"{save_location}/{new_name}.xlsx", index=False, engine="openpyxl")