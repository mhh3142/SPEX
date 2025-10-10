import requests
import json
import base64

""" 
    When you successfully request access the api returns a dictionary of the form {'access_token': '...', 'token_type': 'Bearer', 'expires_in': 3600}
    this function just returns the access token.
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
    Formats the information from get_access_token into a more practical way, also writes in the base_url. I think it makes more sense for the api client to handle base_url
    structure wise, it makes main neater.
"""
def get_base_and_headers(client_id: str, client_secret: str) -> tuple:

    base_url = "http://api.spotify.com/v1"
    headers = {
        "Authorization": "Bearer " + get_access_token(client_id=client_id, client_secret=client_secret)
    }

    return base_url, headers

""" The repeat code for when I make a request to the api. It's poorly done it needs some error protection """
def get_request(url: str, headers: str) -> str:

    response = requests.get(url=url, headers=headers)

    if response.ok:
        json_response = json.loads(response.content)
        return json_response
    else:
        return f"fetch error: {response.status_code}" # Change this so that it throws an actual error and stop the program where it is. Don't want funny bits of missing data
    
""" This returns a list of dictionaries, where each dictionary represents data about an individual track. It stores more than we would like to display but I feel that some of
    the extra information is useful. Could even store more information than i've currently got. Might get rid of the whole nested dictionary thing here. This is also 
    including some external_url stuff which I don't need
"""
def get_playlist_data(base_url: str, headers: str, playlist_id: str) -> list[dict]: # I will try to fix this to do more than 100 songs. Avoid my recursion solution if possible

    playlist_page = get_request(url=f"{base_url}/playlists/{playlist_id}", headers=headers)

    playlist = {
        "name": playlist_page["name"],
        "items": []
    }

    for item in playlist_page["tracks"]["items"]:

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

        playlist["items"].append(track_dict)

    return playlist