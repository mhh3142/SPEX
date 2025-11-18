import base64
from dataclasses import dataclass
import json
import time
from typing import Any, Optional, Dict

import requests

@dataclass
class ClientDetails:
    
    id: str
    secret: str
    base_url: Optional[str]
    access_token: Optional[str]
    headers: Optional[Dict]
    wait_time: Optional[int]

@dataclass
class ApiResult:
    
    data: Optional[Any]
    status: Optional[int]
    error: Optional[str]

""" 
    Uses client_id and client_secret to request auth info from the api. Function returns access token. This function follows the client credentials flow from
    spotify web api documentation
"""
def get_access_token(client_id: str, client_secret: str) -> str:
    
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    auth_url = "https://accounts.spotify.com/api/token"
    auth_headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    auth_body = {"grant_type": "client_credentials"}
    json_response = requests.post(url=auth_url, headers=auth_headers, data=auth_body) # needs error handling
    response = json.loads(json_response.content)
    
    return response["access_token"]

def set_client(client_id: str, client_secret: str) -> ClientDetails:

    base_url = "http://api.spotify.com/v1"
    access_token = get_access_token(client_id=client_id, client_secret=client_secret)
    headers = {
        "Authorization": "Bearer " + access_token
    }
    wait_time = 0

    return ClientDetails(id=client_id, secret=client_secret, base_url=base_url, access_token=access_token, headers=headers, wait_time=wait_time)

def update_client_tokens(client: ClientDetails) -> ClientDetails:

    client.access_token = get_access_token(client_id=client.id, client_secret=client.secret)
    client.headers = {
        "Authorization": "Bearer " + client.access_token
    }

    return client

""" 
    The repeat code for when I make a request to the api.
    - Might need to return new headers if a reauthentication is done. Gonna take some time to figure this out.
"""
# THIS NEEDS TO RETURN THE CLIENT AS THE CLIENT COULD BE UPDATED
def make_request(client: ClientDetails, url: str) -> tuple[ApiResult, ClientDetails]: # watch if time.sleep(0) is slower than an if

    time.sleep(client.wait_time)

    try:
        json_response = requests.get(url=url, headers=client.headers)
        json_response.raise_for_status()
        response = json.loads(json_response.content)

        return (ApiResult(data=response, status=json_response.status_code, error=None), client)

    except requests.exceptions.HTTPError as reqerr:
        
        if reqerr.response.status_code == 401:
            
            client = update_client_tokens(client=client)

            try:

                json_retry_response = requests.get(url=url, headers=client.headers)
                json_retry_response.raise_for_status()
                retry_response = json.loads(json_retry_response.content)

                return (ApiResult(data=retry_response, status=json_retry_response.status_code, error=None), client)
            
            except requests.exceptions.HTTPError as retry_reqerr:
                
                return (ApiResult(data=None, status=retry_reqerr.response.status_code, error=retry_reqerr.response.json().get("error", {}).get("message", "No error message provided")), client)
            
            except json.decoder.JSONDecodeError as retry_jsonerr:
                
                return (ApiResult(data=None, status=json_retry_response.status_code, error=""), client) # figure out suitable error
        
        elif reqerr.response.status_code == 429:

            if client.wait_time == 0:
                client.wait_time = 0.2
            else:
                client.wait_time *= 2

            time.sleep(client.wait_time)

            try:

                json_retry_response = requests.get(url=url, headers=client.headers)
                json_retry_response.raise_for_status()
                retry_response = json.loads(json_retry_response.content)

                return (ApiResult(data=retry_response, status=json_retry_response.status_code, error=None), client)

            except requests.exceptions.HTTPError as retry_reqerr:
                
                return (ApiResult(data=None, status=retry_reqerr.response.status_code, error=retry_reqerr.response.json().get("error", {}).get("message", "No error message provided")), client)
            
            except json.decoder.JSONDecodeError as retry_jsonerr:
                
                return (ApiResult(data=None, status=json_retry_response.status_code, error=""), client)
        else:
            return (ApiResult(data=None, status=json_response.status_code, error=reqerr.response.json().get("error", {}).get("message", "No error message provided")), client)
        
    except json.decoder.JSONDecodeError as jsonerr:
        return (ApiResult(data=None, status=json_response.status_code, error=""), client)
    
""" 
    - Returns a list of dictionaries, where each dictionary represents data about an individual track. 
    - It stores more than we would like to display but I feel that some of the extra information is useful. Could even store more information than i've currently got. 
    Might get rid of the whole nested dictionary thing here. This is also including some external_url stuff which I don't need.
    - In summary, it loads a pages information, checks if there are any nested pages, and if there are it calls itself on the nested page and appends the data. Once it hits
    the deepest page it returns that pages data and at each unwind it just appends more data.
"""
def load_tracks(client: ClientDetails, playlist_page: dict) -> tuple[list[dict], ClientDetails]:

    tracks = []
    for item in playlist_page["items"]:

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

        item_album, client = make_request(client=client, url=f"{client.base_url}/albums/{track_dict["trackRequest"]["albumId"]}")

        if item_album.data is not None:
            track_dict["albumRequest"]["upc"] = item_album.data["external_ids"]["upc"]
            track_dict["albumRequest"]["copyRights"] = item_album.data["copyrights"]
            track_dict["albumRequest"]["label"] = item_album.data["label"]
        else:
            track_dict["albumRequest"]["upc"] = "UNAVAILABLE"
            track_dict["albumRequest"]["copyRights"] = "UNAVAILABLE"
            track_dict["albumRequest"]["label"] = "UNAVAILABLE"

        tracks.append(track_dict)
    
    if playlist_page["next"] is not None:
        new_page, client = make_request(client=client, url=playlist_page["next"])
        if new_page.data is not None:
            tracks.extend(load_tracks(client=client, playlist_page=new_page.data))
    
    return (tracks, client)
    
"""
    Calls load_playlist_data to get the track list data, packages the info up and sends it. This function is designed to keep main neat. Unfortunately we have to repeat
    an api call to get the name of the playlist, I think this is unavoidable as the info needs to be in two different places at once. I think decorating get_request with 
    functools.cache should mean that it won't call the api again it'll use the last call.
    Another useful one is functools.lru_cache
"""
def get_playlist(client: ClientDetails, playlist_id: str) -> tuple[ApiResult, ClientDetails]:

    playlist, client = make_request(client=client, url=f"{client.base_url}/playlists/{playlist_id}")
    if playlist.data is not None:

        items, client = load_tracks(client=client, playlist_page=playlist.data)
        playlist_dict = {
            "name": playlist.data["name"],
            "items": items
        }
        # error is expected to be none in the line below but just to be safe pass it from playlist.error
        return (ApiResult(data=playlist_dict, status=playlist.status, error=playlist.error), client)
    else:
        return (playlist, client)