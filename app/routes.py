from fastapi import APIRouter, Depends, HTTPException, Response
from .dependencies import get_youtube_api
from .models import Comment
from googleapiclient.discovery import Resource
from typing import List
import csv
import os

router = APIRouter()

@router.get("/comments/{video_id}")
async def get_comments(video_id: str, youtube: Resource = Depends(get_youtube_api)):
    # Make the request to the YouTube API to fetch comments
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100
    )

    comments = []
    while request:
        response = request.execute()
        for item in response.get('items', []):
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'author': comment['authorDisplayName'],
                'channel_id': comment['authorChannelId']['value'],
                'text': comment['textDisplay'],
                'published_at': comment['publishedAt']
            })
        request = youtube.commentThreads().list_next(request, response)

    # Use the current working directory as the base path
    current_directory = os.getcwd()
    csv_file_path = os.path.join(current_directory, f'comments_{video_id}.csv')

    # Write comments to the CSV file
    with open(csv_file_path, 'w', newline='') as csvfile:
        fieldnames = ['author', 'channel_id', 'text', 'published_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comments)

    # Return success message
    return {
        "message": f"Comments for video ID '{video_id}' have been saved to {csv_file_path}"
    }
