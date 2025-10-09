import requests
import json
import base64

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
    json_result = json.loads(response.content) # This is a dictionary of the form {'access_token': '...', 'token_type': 'Bearer', 'expires_in': 3600}
    access_token = json_result["access_token"]
    
    return access_token

def get_request(url: str, headers: str) -> str:

    response = requests.get(url=url, headers=headers)

    if response.ok:
        json_response = json.loads(response.content)
        return json_response
    else:
        return f"fetch error: {response.status_code}" # Maybe change this error to be throw an actual error and stop the program