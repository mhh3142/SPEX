import re

import pandas as pd

""" Uses regex to convert the date from Spotify's YYYY-MM-DD format into Lime Blue's DD/MM/YY format. Spotify provides a precision value for the date. Lime Blue has a procedure 
    for dates given to poor precision. add that functionality to my function, it's important.
"""
def format_date(date: str) -> str:

    split_list = re.split(pattern=r"-{1}", string=date)
    split_list.reverse()

    return "/".join(split_list)

""" Uses regex to convert the time from Spotify's time format in ms into Lime Blues hh:mm:ss format. """
def format_time(time: int) -> str:

    time_seconds = round(time / 1000)
    
    minutes, seconds = divmod(time_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    return f"{hours:02}:{minutes:02}:{seconds:02}"

"""
    For this function we could do more work to keep everything clean, especially around None type values.
    I need to decide if I want to include Album Type and I need to fix the bugs with Publishing and Copy. Might get rid of the nested dictionary structure in the api client
    so bare that in mind as I would need to change some of this code
"""
def playlist_frame_formatter(playlist_raw: list[dict]) -> pd.DataFrame:

    playlist_clean = []

    for item in playlist_raw:

        item_dict_clean = {}

        item_dict_clean["Release Artist"] = ", ".join(artist["name"] for artist in item["trackRequest"]["releaseArtists"])
        item_dict_clean["Track Band / Artist Name"] = ", ".join(artist["name"] for artist in item["trackRequest"]["featuredArtists"])
        item_dict_clean["Recording Title"] = item["trackRequest"]["trackTitle"]
        # item_dict_clean["Subtitle / Version / Mixname"]
        item_dict_clean["ISRC"] = item["trackRequest"]["isrc"]
        item_dict_clean["Album Title"] = item["trackRequest"]["albumTitle"]
        item_dict_clean["Catalogue Number"] = item["albumRequest"]["upc"]
        item_dict_clean["Original Release Label"] = item["albumRequest"]["label"] # Need to talk to mario about how relevant this bit is
        item_dict_clean["Duration (hh:mm:ss)"] = format_time(item["trackRequest"]["trackDuration"])
        item_dict_clean["Release Date (DD/MM/YYYY)"] = format_date(item["trackRequest"]["releaseDate"])
        # item_dict_clean["Album Type"] # = item["trackRequest"]["albumType"]
        # item_dict_clean["Publishing"] # This can be found in albumRequest/copyRights
        # item_dict_clean["Copy"] # This can be found in albumRequest/copyRights
        item_dict_clean["Source"] = "Spotify"

        playlist_clean.append(item_dict_clean)

    return pd.DataFrame(playlist_clean)