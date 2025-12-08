# Offline YouTube

A simple offline YouTube clone that lets you download and browse videos and shorts from your favorite channels.

## Features

- 📹 **Videos** - Browse and watch downloaded videos
- 🎥 **Shorts** - Watch vertical videos in a TikTok-like interface
- 🔍 **Search** - Search through all your downloaded content
- 💬 **Comments** - View top comments and replies
- 📱 **Responsive** - Works on desktop, tablet, and mobile
- ⚡ **Fast** - No internet required after downloading

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Channels

Edit `channels.json` to add YouTube channels you want to download:

```json
[
  {
    "channel_name": "channelname",
    "video_count": 10
  }
]
```

### 3. Download Videos

Run the downloader:

```bash
python yt.py
```

Videos and shorts will be saved to the `videos/` directory with comments.

### 4. Start the Server

```bash
python backend.py
```

The server runs on `http://localhost:8000`

## Usage

- Open `http://localhost:8000` in your browser
- Browse the **Videos** tab to watch downloaded videos
- Switch to **Shorts** tab for vertical video experience
- Use **Search** tab to find content by title or channel name

## File Structure

```
offline-yt/
├── videos/                 # Downloaded videos organized by channel
├── static/                 # CSS and JavaScript
├── index.html             # Frontend
├── backend.py             # FastAPI server
├── yt.py                  # Video downloader
└── channels.json          # Channel configuration
```

## Configuration

Edit `yt.py` to customize:
- `QUALITY` - Download quality (720, 480, 360)
- `MAX_COMMENTS` - Number of comments to download
- `DOWNLOAD_COMMENTS` - Enable/disable comment downloading

## Network Access

To access from another device on your network:
1. Find your machine's IP address
2. Open `http://<your-ip>:8000` on another device

## Notes

- Videos are stored with their video IDs: `Title [video_id].webm`
- Comments are downloaded with metadata for offline viewing
- Already downloaded videos are skipped on subsequent runs
