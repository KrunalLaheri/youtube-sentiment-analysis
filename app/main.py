from fastapi import FastAPI
from .routes import router
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request, HTTPException, status, APIRouter
from .dependencies import get_youtube_api, get_youtube_api_key
import httpx
app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

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

        return live_comments

# http://1270.0.01:8000/fetch_live_comments?video_id=YOUR_VIDEO_ID
