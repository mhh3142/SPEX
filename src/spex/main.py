import argparse
import os
import re

from dotenv import load_dotenv

from spex.api_client import get_playlist
from spex.api_client import set_client
from spex.exporter import export_to_excel
from spex.formatter import playlist_frame_formatter

"""
    Handles command line input using argparse, extracts the playlist id from the playlist url using regex, loads secret information from .env using python-dotenv, finally
    runs 

    io.BytesIO could be the thing that speeds my life up. It avoids disc operations and puts it on RAM instead which is quicker apparently. Doesn't have to be BytesIO, theres others
    for different data types
"""
def main() -> None:

    parser = argparse.ArgumentParser(description="Read playlist url and launch program")
    parser.add_argument("playlist_link", type=str, help="Link to Spotify Playlist")
    args = parser.parse_args()
    link = args.playlist_link

    # error handle here to deal with bad url inputs
    # give the option to enter a playlist_id manually
    pattern = r"https:\/\/open.spotify.com\/playlist\/(.*)\?"
    match = re.search(pattern=pattern, string=link)
    playlist_id = match.group(1)

    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    client = set_client(client_id=client_id, client_secret=client_secret)

    for i in range(3):

        playlist, client = get_playlist(client=client, playlist_id=playlist_id)

        if playlist.data is not None:
            break
        else:
            if playlist.status == 400 or playlist.status == 404:
                if i < 2:
                    print("Time to redo the thing. This isn't over yet :-)")
                    playlist_id = "something new that we've updated"
                else:
                    return
            elif playlist.status == 401 or playlist.status == 429:
                # consider trying one more time. Maybe we've got unlucky
                pass
            elif playlist.status >= 500:
                print("Error with Spotify server")
            else:
                return
            
    playlist_frame = playlist_frame_formatter(playlist_raw=playlist.data["items"])
    export_to_excel(playlist_name=playlist.data["name"], playlist_frame=playlist_frame)

if __name__ == "__main__":
    main()