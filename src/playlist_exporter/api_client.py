import json
import base64

import requests

""" 
    Uses client_id and client_secret to request auth info from the api. Function returns access token. This function follows the client credentials flow from
    spotify web api documentation
"""
def get_access_token(client_id: str, client_secret: str) -> str:
    
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    body = {"grant_type": "client_credentials"}
    response = requests.post(url=url, headers=headers, data=body)
    json_result = json.loads(response.content)
    access_token = json_result["access_token"]
    
    return access_token

""" 
    Calls the get_access_token to get the auth code, packages the info up and sends it. This function is designed to keep main neat.
"""
def get_base_and_headers(client_id: str, client_secret: str) -> tuple:

    base_url = "http://api.spotify.com/v1"
    headers = {
        "Authorization": "Bearer " + get_access_token(client_id=client_id, client_secret=client_secret)
    }

    return base_url, headers

""" 
    The repeat code for when I make a request to the api.
"""
def get_request(url: str, headers: dict): # need to figure out what the type of the return is
    # Should add some error handling to this function
    response = requests.get(url=url, headers=headers)

    if response.ok:
        json_response = json.loads(response.content)
        return json_response
    else:
        return f"fetch error: {response.status_code}" # This should throw this error message and stop stuff cus it's a nightmare to find this error
    
""" 
    - Returns a list of dictionaries, where each dictionary represents data about an individual track. 
    - It stores more than we would like to display but I feel that some of the extra information is useful. Could even store more information than i've currently got. 
    Might get rid of the whole nested dictionary thing here. This is also including some external_url stuff which I don't need.
    - In summary, it loads a pages information, checks if there are any nested pages, and if there are it calls itself on the nested page and appends the data. Once it hits
    the deepest page it returns that pages data and at each unwind it just appends more data.
"""
def load_playlist_data(page_url: str, base_url: str, headers: dict) -> list[dict]:

    playlist_page = get_request(url=page_url, headers=headers)
    playlist = []

    for item in playlist_page["items"]: # load it's own data using the formatting that i've already done

        track_dict = {}
        track_dict["trackRequest"] = {}
        track_dict["albumRequest"] = {}

        track_dict["trackRequest"]["releaseArtists"] = item["track"]["album"]["artists"]
        track_dict["trackRequest"]["featuredArtists"] = item["track"]["artists"]
        track_dict["trackRequest"]["trackTitle"] = item["track"]["name"]
        track_dict["trackRequest"]["trackId"] = item["track"]["id"]
        track_dict["trackRequest"]["trackDuration"] = item["track"]["duration_ms"]
        track_dict["trackRequest"]["isrc"] = item["track"]["external_ids"]["isrc"]
        track_dict["trackRequest"]["albumTitle"] = item["track"]["album"]["name"]
        track_dict["trackRequest"]["albumId"] = item["track"]["album"]["id"]
        track_dict["trackRequest"]["albumType"] = item["track"]["album"]["album_type"]
        track_dict["trackRequest"]["releaseDate"] = item["track"]["album"]["release_date"]

        item_album = get_request(url=f"{base_url}/albums/{track_dict["trackRequest"]["albumId"]}", headers=headers)
        track_dict["albumRequest"]["upc"] = item_album["external_ids"]["upc"]
        track_dict["albumRequest"]["copyRights"] = item_album["copyrights"]
        track_dict["albumRequest"]["label"] = item_album["label"]

        playlist.append(track_dict)
    
    # if nesting possible, then nest and extend new data onto own data
    if playlist_page["next"] is not None: # Might be null type sometimes
        playlist.extend(load_playlist_data(page_url=playlist_page["next"], base_url=base_url, headers=headers))
    
    return playlist
    
"""
    Calls load_playlist_data to get the track list data, packages the info up and sends it. This function is designed to keep main neat. Unfortunately we have to repeat
    an api call to get the name of the playlist, I think this is unavoidable as the info needs to be in two different places at once.
"""
def get_playlist(base_url: str, headers: dict, playlist_id: str) -> dict:
    
    playlist = {
        "name": get_request(url=f"{base_url}/playlists/{playlist_id}", headers=headers)["name"],
        "items": load_playlist_data(page_url=f"{base_url}/playlists/{playlist_id}/tracks?offset=0&limit=100", base_url=base_url, headers=headers)
    }

    return playlist