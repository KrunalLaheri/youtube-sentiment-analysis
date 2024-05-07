import time
from googleapiclient.discovery import build

# Import the necessary AWS Lambda libraries
import boto3

# Environment variables
API_KEY = 'YOUTUBE_API_KEY'  # Set this in your Lambda function configuration
LIVE_VIDEO_ID = 'YOUTUBE_VIDEO_ID'  # Set this in your Lambda function configuration

# Build the YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

def monitor_live_chat(event, context):
    # Get live chat ID
    response = youtube.videos().list(
        part='liveStreamingDetails',
        id=LIVE_VIDEO_ID
    ).execute()

    live_chat_id = response['items'][0]['liveStreamingDetails']['activeLiveChatId']

    # Variable to store next page token
    next_page_token = None

    # Continuously monitor new comments
    while True:
        # Retrieve live chat messages
        response = youtube.liveChatMessages().list(
            liveChatId=live_chat_id,
            part='snippet,authorDetails',
            pageToken=next_page_token
        ).execute()

        # Process each message
        for message in response['items']:
            author = message['authorDetails']['displayName']
            text = message['snippet']['displayMessage']
            print(f"{author}: {text}")

        # Update the next page token
        next_page_token = response.get('nextPageToken')
        print("===========>Next page token:", next_page_token)

        # Wait for a few seconds before polling again
        time.sleep(5)