import base64
from dataclasses import dataclass
import json
import time
from typing import Any, Optional

import requests

@dataclass
class ApiResult:
    
    data: Optional[Any]
    status: Optional[int]
    error: Optional[str]

class ApiClient:

    def __init__(self, client_id: str, client_secret: str):

        self.client_id = client_id
        self.client_secret = client_secret
        
        self.access_token = None
        self.refresh_token = None # this isn't available for client credentials flow
        self.headers = None
        
        self.base_url = "http://api.spotify.com/v1"
        self.wait_time = 0

        self.set_access_tokens()
        self.set_headers()

    """ Client credentials flow """
    def set_access_tokens(self):

        auth_string = self.client_id + ":" + self.client_secret
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        auth_url = "https://accounts.spotify.com/api/token"
        auth_headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        body = {"grant_type": "client_credentials"}
        json_response = requests.post(url=auth_url, headers=auth_headers, data=body)
        response = json.loads(json_response.content) # could do with some error handling here
        
        self.access_token = response["access_token"]

    def set_headers(self):

        self.headers = {
            "Authorization": "Bearer " + self.access_token
        }

    def request(self, url: str) -> ApiResult:

        time.sleep(self.wait_time)

        try:
            json_response = requests.get(url=url, headers=self.headers)
            json_response.raise_for_status()
            response = json.loads(json_response.content)

            return ApiResult(data=response, status=json_response.status_code, error=None)

        except requests.exceptions.HTTPError as reqerr:
            
            if reqerr.response.status_code == 401:

                self.set_access_tokens()
                try:
                    
                    json_retry_response = requests.get(url=url, headers=self.headers)
                    json_retry_response.raise_for_status()
                    retry_response = json.loads(json_retry_response.content)

                    return ApiResult(data=retry_response, status=json_retry_response.status_code, error=None)
                
                except requests.exceptions.HTTPError as retry_reqerr:
                
                    return ApiResult(data=None, status=retry_reqerr.response.status_code, error=retry_reqerr.response.json().get("error", {}).get("message", "No error message provided"))
                
                except json.decoder.JSONDecodeError as retry_jsonerr:
                
                    return ApiResult(data=None, status=json_retry_response.status_code, error="")
            
            elif reqerr.response.status_code == 429:

                if self.wait_time == 0:
                    self.wait_time = 0.2
                else:
                    self.wait_time *= 2

                time.sleep(self.wait_time)

                try:
                    
                    json_retry_response = requests.get(url=url, headers=self.headers)
                    json_retry_response.raise_for_status()
                    retry_response = json.loads(json_retry_response.content)

                    return ApiResult(data=retry_response, status=json_retry_response.status_code, error=None)

                except requests.exceptions.HTTPError as retry_reqerr:
                    
                    return ApiResult(data=None, status=retry_reqerr.response.status_code, error=retry_reqerr.response.json().get("error", {}).get("message", "No error message provided"))
                
                except json.decoder.JSONDecodeError as retry_jsonerr:
                    
                    return ApiResult(data=None, status=json_retry_response.status_code, error="")
            else:
                return ApiResult(data=None, status=json_response.status_code, error=reqerr.response.json().get("error", {}).get("message", "No error message provided"))
        
        except json.decoder.JSONDecodeError as jsonerr:
            return ApiResult(data=None, status=json_response.status_code, error="")
        
    def __load_tracks(self, playlist_page: dict) -> list[dict]:

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

            item_album = self.request(url=f"{self.base_url}/albums/{track_dict["trackRequest"]["albumId"]}")

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
            new_page = self.request(url=playlist_page["next"])
            if new_page.data is not None:
                tracks.extend(self.__load_tracks(new_page.data))
        
        return tracks
    
    def get_playlist(self, playlist_id: str) -> dict | None:

        playlist = self.request(url=f"{self.base_url}/playlists/{playlist_id}")
        if playlist.data is not None:
            playlist_dict = {
                "name": playlist.data["name"],
                "items": self.__load_tracks(playlist_page=playlist.data)
            }
            return playlist_dict # could return an ApiResult(data=playlist_dict, ...)
        else:
            return None # return ApiResult(data=None, ...)