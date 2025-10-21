import argparse
import os
import re

from dotenv import load_dotenv

from playlist_exporter.api_client import get_base_and_headers
from playlist_exporter.api_client import get_playlist
from playlist_exporter.exporter import export_to_excel
from playlist_exporter.formatter import playlist_frame_formatter

"""
    I HAD LISTED REQUESTS TWICE IN THE .TOML FILE, WHEN I MERGE THIS BRANCH INTO THE MAIN BRANCH MAKE A NOTE ON COMMIT.
    ALSO NOW THAT I THINK OF IT MAYBE PYTEST SHOULD BE IN DEV DEPENDENCIES.
"""


"""
    Handles command line input using argparse, extracts the playlist id from the playlist url using regex, loads secret information from .env using python-dotenv, finally
    runs 
"""

def main() -> None:

    # using argparse to store the spotify link into a link variable
    parser = argparse.ArgumentParser(description="Read playlist url and launch program")
    parser.add_argument("playlist_link", type=str, help="Link to Spotify Playlist")
    args = parser.parse_args()
    link = args.playlist_link

    # using regex to extract the playlist_id from the spotify link
    pattern = r"https:\/\/open.spotify.com\/playlist\/(.*)\?"
    match = re.search(pattern=pattern, string=link)
    playlist_id = match.group(1)

    # loads the LimeBlue secret information
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    base_url, headers = get_base_and_headers(client_id=client_id, client_secret=client_secret)

    playlist_dict_raw = get_playlist(base_url=base_url, headers=headers, playlist_id=playlist_id)

    playlist_frame = playlist_frame_formatter(playlist_raw=playlist_dict_raw["items"])

    export_to_excel(playlist_name=playlist_dict_raw["name"], playlist_frame=playlist_frame)

if __name__ == "__main__":
    main()