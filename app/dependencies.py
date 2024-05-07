import os
from googleapiclient.discovery import build
from fastapi import Depends

def initialize_youtube_api(api_key: str):
    return build("youtube", "v3", developerKey=api_key)

def get_youtube_api():
    # api_key = os.getenv('YOUTUBE_API_KEY')
    return initialize_youtube_api("YOUTUBE_API_KEY")

def get_youtube_api_key():
    return "YOUTUBE_API_KEY"

