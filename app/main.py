from .routes import router
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request, HTTPException, status, APIRouter, BackgroundTasks
from .dependencies import get_youtube_api, get_youtube_api_key
import httpx
import boto3
import json
import googleapiclient.discovery
import time

# Project configuration START =================================================================================================
app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

kinesis_client = boto3.client('kinesis', 
                              region_name='us-east-1',
                              aws_access_key_id='AWS_ACCESS_KEY',
                              aws_secret_access_key='AWS_SECRET_KEY',
                            )

# Project configuration END ===================================================================================================


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Render the HTML page using the template
    return templates.TemplateResponse("index.html", {"request": request})

app.include_router(router, prefix="/api/v1", tags=["comments"])


# Replace with your own API key
API_KEY = get_youtube_api_key()
@app.get("/fetch_live_comments")
async def fetch_live_comments(video_id: str):
    # Construct the URL to get video details
    url_video = f'https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={video_id}&key={API_KEY}'

    async with httpx.AsyncClient() as client:
        # Fetch live streaming details of the video
        response = await client.get(url_video)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch video details")

        data = response.json()
        
        # Check if liveStreamingDetails is available
        if not data['items']:
            raise HTTPException(status_code=404, detail="Video not found")
        
        live_chat_id = data['items'][0]['liveStreamingDetails'].get('activeLiveChatId')
        if not live_chat_id:
            raise HTTPException(status_code=404, detail="Live chat is not active for this video")

        # Construct the URL to fetch live chat messages
        url_chat = f'https://www.googleapis.com/youtube/v3/liveChat/messages?liveChatId={live_chat_id}&part=snippet,authorDetails&key={API_KEY}'

        # Fetch live chat messages
        chat_response = await client.get(url_chat)
        if chat_response.status_code != 200:
            raise HTTPException(status_code=chat_response.status_code, detail="Failed to fetch chat messages")

        chat_data = chat_response.json()

        # Process and return the chat messages
        live_comments = []
        for message in chat_data['items']:
            comment = {
                "author": message['authorDetails']['displayName'],
                "profile_image": message['authorDetails']['profileImageUrl'],
                "text": message['snippet']['displayMessage'],
                "time": message['snippet']['publishedAt']
            }
            live_comments.append(comment)
            # print("======================================================================comment",comment)
            # print("================================================================type(comment)",type(comment))
            live_comments_json = json.dumps(comment)

            try:
                response = kinesis_client.describe_stream(StreamName='YoutubeCommentStream')
                print("Credentials and permissions are correct.")
            except Exception as e:
                print(f"Error: {e}")

            response = kinesis_client.put_record(
                StreamName='YoutubeCommentStream',  # Replace with your Kinesis Data Stream name
                Data=live_comments_json,
                PartitionKey='First use'  # Use a suitable partition key for your data
            )


        return live_comments

# http://1270.0.01:8000/fetch_live_comments?video_id=YOUR_VIDEO_ID

# Continous comment retrival START ==================================================================================================================================

# Your live video ID here
live_video_id = 'LIVE_VIDEO_ID'

# Build the YouTube API client
youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=API_KEY)

# Function to monitor live chat comments
def monitor_live_chat():
    # Get live chat ID
    response = youtube.videos().list(
        part='liveStreamingDetails',
        id=live_video_id
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
        print("================================================================>next_page_token: ",next_page_token)

        # Wait for a few seconds before polling again
        time.sleep(5)

# Endpoint to start monitoring live chat
@app.get("/start-monitoring")
async def start_monitoring(background_tasks: BackgroundTasks):
    # Start monitoring live chat in a background task
    background_tasks.add_task(monitor_live_chat)
    return {"status": "Monitoring started"}

# Continous comment retrival END ====================================================================================================================================

# Endpoint to triger lambda function START ==========================================================================================================================
lambda_client = boto3.client('lambda', region_name='us-east-1',
                              aws_access_key_id='AWS_ACCESS_KEY_ID',
                              aws_secret_access_key='AWS_SECRET_KEY_ID',)
@app.get("/trigger-lambda")
async def trigger_lambda_function():
    # Define the payload
    payload = {
        "key1": "request.key1",
        "key2": "request.key2"
    }

    # Convert payload to JSON
    json_payload = json.dumps(payload)

    # Invoke the Lambda functionRuntime.ImportModuleError\", \"requestId\": \"ce45cc90-ed94-406a-b7ef-70e0b9cee5ac\", \"stackTrace\": []}"}
    try:
        response = lambda_client.invoke(
            FunctionName='LAMBDA_FUNCTION_NAME',
            InvocationType='RequestResponse',  # 'Event' for asynchronous, 'RequestResponse' for synchronous
            Payload=json_payload
        )

        # Extract the response payload
        response_payload = response['Payload'].read().decode('utf-8')

        # Return the Lambda function's response
        return {
            "response": response_payload
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error invoking Lambda: {str(e)}")

# Endpoint to triger lambda function END ============================================================================================================================
