from io import BytesIO
from io import StringIO
import os
import re

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import pandas as pd

from spex.api_client import get_base_and_headers
from spex.api_client import get_playlist
from spex.formatter import playlist_frame_formatter

app = FastAPI()

def get_playlist_dict(playlist_id: str) -> dict:

    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    base_url, headers = get_base_and_headers(client_id=client_id, client_secret=client_secret)

    playlist = get_playlist(base_url=base_url, headers=headers, playlist_id=playlist_id)

    return playlist

@app.get("/")
async def root() -> dict:
    
    return {"message": "Welcome to SPEX, visit /playlists and supply your desired playlist id as a query"}

@app.get("/playlists/raw")
async def playlist_raw(playlist_id: str) -> dict:

    return get_playlist_dict(playlist_id=playlist_id)

@app.get("/playlists/csv")
async def get_csv_data(playlist_id: str) -> StreamingResponse: # This one mash up some of my formatting, I think it's a csv to excel thing
    
    playlist = get_playlist_dict(playlist_id=playlist_id)
    playlist_name = playlist["name"]
    df = playlist_frame_formatter(playlist_raw=playlist["items"])

    # loads the csv into ram, this is better than storing on disc
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    return StreamingResponse(
        content=buffer,
        headers={"Content-Disposition": f"attachment; filename={playlist_name}.csv"},
        media_type="text/csv"
    )

@app.get("/playlists/xlsx")
async def get_excel_data(playlist_id: str) -> StreamingResponse:

    playlist = get_playlist_dict(playlist_id=playlist_id)
    playlist_name = playlist["name"]
    df = playlist_frame_formatter(playlist_raw=playlist["items"])

    buffer = BytesIO()
    with pd.ExcelWriter(path=buffer, engine="openpyxl") as writer: # ExcelWriter is apparently much better at dealing with complexities of excel than pd.to_excel
        df.to_excel(excel_writer=writer, index=False)
    buffer.seek(0)

    return StreamingResponse(
        content=buffer,
        headers={"Content-Disposition": f"attachment; filename={playlist_name}.xlsx"},
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )