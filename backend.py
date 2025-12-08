from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel

app = FastAPI()

# Configuration
VIDEOS_DIR = "videos"

class VideoItem(BaseModel):
    video_id: str
    title: str
    channel: str
    duration: int
    thumbnail_path: str
    type: str  # "video" or "shorts"

class CommentsResponse(BaseModel):
    comments: List[Dict[str, Any]]

def get_video_thumbnail(video_path: str) -> str:
    """Generate thumbnail from video file"""
    # For offline content, we'll use a placeholder
    # In a real scenario, we might extract actual thumbnails
    return "/static/placeholder.jpg"

def get_all_videos() -> List[Dict[str, Any]]:
    """Scan videos folder and return all videos with metadata"""
    videos = []
    
    # Process channel directories
    for channel_dir in os.listdir(VIDEOS_DIR):
        channel_path = os.path.join(VIDEOS_DIR, channel_dir)
        if not os.path.isdir(channel_path):
            continue
        
        # Check videos folder
        videos_folder = os.path.join(channel_path, "videos")
        if os.path.exists(videos_folder):
            for video_file in os.listdir(videos_folder):
                if video_file.endswith(('.mp4', '.mkv', '.webm')):
                    # Extract video_id from filename: "Title [video_id].ext"
                    base_name = os.path.splitext(video_file)[0]
                    
                    # Try to extract video ID from brackets
                    if '[' in base_name and ']' in base_name:
                        video_id = base_name.split('[')[-1].rstrip(']').strip()
                    else:
                        video_id = base_name
                    
                    # Look for meta.json file
                    meta_file = os.path.join(channel_path, "comments", video_id, "meta.json")
                    
                    if os.path.exists(meta_file):
                        try:
                            with open(meta_file, 'r', encoding='utf-8') as f:
                                meta = json.load(f)
                                videos.append({
                                    "video_id": meta.get("video_id", video_id),
                                    "title": meta.get("title", base_name),
                                    "channel": meta.get("channel", channel_dir),
                                    "duration": meta.get("duration", 0),
                                    "type": "video",
                                    "file_path": os.path.join(channel_dir, "videos", video_file),
                                    "comments_path": os.path.join(channel_dir, "comments", video_id)
                                })
                        except:
                            pass
        
        # Check shorts folder
        shorts_folder = os.path.join(channel_path, "shorts")
        if os.path.exists(shorts_folder):
            for video_file in os.listdir(shorts_folder):
                if video_file.endswith(('.mp4', '.mkv', '.webm')):
                    # Extract video_id from filename: "Title [video_id].ext"
                    base_name = os.path.splitext(video_file)[0]
                    
                    # Try to extract video ID from brackets
                    if '[' in base_name and ']' in base_name:
                        video_id = base_name.split('[')[-1].rstrip(']').strip()
                    else:
                        video_id = base_name
                    
                    # Look for meta.json file
                    meta_file = os.path.join(channel_path, "comments", video_id, "meta.json")
                    
                    if os.path.exists(meta_file):
                        try:
                            with open(meta_file, 'r', encoding='utf-8') as f:
                                meta = json.load(f)
                                videos.append({
                                    "video_id": meta.get("video_id", video_id),
                                    "title": meta.get("title", base_name),
                                    "channel": meta.get("channel", channel_dir),
                                    "duration": meta.get("duration", 0),
                                    "type": "shorts",
                                    "file_path": os.path.join(channel_dir, "shorts", video_file),
                                    "comments_path": os.path.join(channel_dir, "comments", video_id)
                                })
                        except:
                            pass
    
    return videos

@app.get("/api/videos", response_model=List[VideoItem])
def get_videos(skip: int = 0, limit: int = 20):
    """Get videos with pagination (randomized)"""
    all_videos = get_all_videos()
    all_videos = [v for v in all_videos if v['type'] == 'video']
    
    # Randomize once and cache could be done, but for simplicity:
    random.seed(42)  # Consistent randomization across requests
    random.shuffle(all_videos)
    
    paginated = all_videos[skip:skip + limit]
    return [VideoItem(
        video_id=v['video_id'],
        title=v['title'],
        channel=v['channel'],
        duration=v['duration'],
        thumbnail_path="/static/placeholder.jpg",
        type=v['type']
    ) for v in paginated]

@app.get("/api/shorts", response_model=List[VideoItem])
def get_shorts(skip: int = 0, limit: int = 10):
    """Get shorts with pagination (randomized, lazy loading)"""
    all_videos = get_all_videos()
    all_videos = [v for v in all_videos if v['type'] == 'shorts']
    
    # Randomize once and cache could be done, but for simplicity:
    random.seed(42)
    random.shuffle(all_videos)
    
    paginated = all_videos[skip:skip + limit]
    return [VideoItem(
        video_id=v['video_id'],
        title=v['title'],
        channel=v['channel'],
        duration=v['duration'],
        thumbnail_path="/static/placeholder.jpg",
        type=v['type']
    ) for v in paginated]

@app.get("/api/videos/search", response_model=List[VideoItem])
def search_videos(query: str = "", skip: int = 0, limit: int = 20):
    """Search videos, shorts, and channels with pagination"""
    all_videos = get_all_videos()
    
    # Filter by query (case-insensitive)
    query_lower = query.lower()
    results = [
        v for v in all_videos
        if query_lower in v['title'].lower() or query_lower in v['channel'].lower()
    ]
    
    # Randomize for variety
    random.seed(42)
    random.shuffle(results)
    
    # Paginate
    paginated = results[skip:skip + limit]
    return [VideoItem(
        video_id=v['video_id'],
        title=v['title'],
        channel=v['channel'],
        duration=v['duration'],
        thumbnail_path="/static/placeholder.jpg",
        type=v['type']
    ) for v in paginated]

@app.get("/api/video/{video_id}")
def get_video_file(video_id: str):
    """Get video file stream"""
    all_videos = get_all_videos()
    
    for video in all_videos:
        if video['video_id'] == video_id:
            file_path = os.path.join(VIDEOS_DIR, video['file_path'])
            if os.path.exists(file_path):
                return FileResponse(file_path, media_type="video/mp4")
    
    raise HTTPException(status_code=404, detail="Video not found")

@app.get("/api/comments/{video_id}")
def get_comments(video_id: str) -> Dict[str, Any]:
    """Get comments for a video"""
    all_videos = get_all_videos()
    
    comments_path = None
    for video in all_videos:
        if video['video_id'] == video_id:
            # comments_path is already the full path from get_all_videos
            comments_path = os.path.join(VIDEOS_DIR, video['comments_path'])
            break
    
    if not comments_path or not os.path.exists(comments_path):
        print(f"Comments not found for {video_id}, path was: {comments_path}")
        raise HTTPException(status_code=404, detail="Comments not found")
    
    # Load comments from top/ directory
    comments = []
    top_dir = os.path.join(comments_path, "top")
    replies_dir = os.path.join(comments_path, "replies")
    
    if os.path.exists(top_dir):
        comment_files = sorted(os.listdir(top_dir))
        for comment_file in comment_files:
            if comment_file.endswith('.json'):
                try:
                    with open(os.path.join(top_dir, comment_file), 'r', encoding='utf-8') as f:
                        comment = json.load(f)
                        comment_id = comment.get('id')
                        
                        # Normalize field names
                        if 'likes' in comment and 'like_count' not in comment:
                            comment['like_count'] = comment['likes']
                        
                        # Load replies if they exist
                        replies = []
                        if os.path.exists(replies_dir):
                            comment_replies_dir = os.path.join(replies_dir, f"c_{comment_file.split('_')[1].split('.')[0]}")
                            if os.path.exists(comment_replies_dir):
                                reply_files = sorted(os.listdir(comment_replies_dir))
                                for reply_file in reply_files:
                                    if reply_file.endswith('.json'):
                                        try:
                                            with open(os.path.join(comment_replies_dir, reply_file), 'r', encoding='utf-8') as rf:
                                                reply = json.load(rf)
                                                # Normalize field names for replies too
                                                if 'likes' in reply and 'like_count' not in reply:
                                                    reply['like_count'] = reply['likes']
                                                replies.append(reply)
                                        except:
                                            pass
                        
                        comment['replies'] = replies
                        comments.append(comment)
                except:
                    pass
    
    return {
        "video_id": video_id,
        "comments": comments
    }

@app.get("/api/video-info/{video_id}")
def get_video_info(video_id: str) -> Dict[str, Any]:
    """Get video metadata"""
    all_videos = get_all_videos()
    
    for video in all_videos:
        if video['video_id'] == video_id:
            return video
    
    raise HTTPException(status_code=404, detail="Video not found")

# Serve static files
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html
@app.get("/")
def read_root():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=16969)
