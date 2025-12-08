from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError
import json
import os
import glob
import time
import shutil

# Configuration
DOWNLOAD_COMMENTS = True
MAX_COMMENTS = 50
MAX_REPLIES = 120
QUALITY = "720"  # Options: "720", "480", "360"

def get_downloaded_videos(videos_dir, shorts_dir):
    """Get list of already downloaded video files with timestamps"""
    downloaded = {}
    for pattern in [f"{videos_dir}/*", f"{shorts_dir}/*"]:
        for file in glob.glob(pattern):
            if os.path.isfile(file):
                # Store filename without extension and its modification time
                filename = os.path.splitext(os.path.basename(file))[0]
                mtime = os.path.getmtime(file)
                downloaded[filename] = (mtime, file)
    return downloaded

def cleanup_old_videos(videos_dir, shorts_dir, video_count, comments_dir):
    """Remove oldest videos if count exceeds video_count"""
    # Get all files with their modification times
    all_files = []
    for pattern in [f"{videos_dir}/*", f"{shorts_dir}/*"]:
        for file in glob.glob(pattern):
            if os.path.isfile(file):
                mtime = os.path.getmtime(file)
                all_files.append((mtime, file))
    
    # Sort by modification time (oldest first)
    all_files.sort()
    
    # Remove oldest files if we exceed video_count
    total_files = len(all_files)
    print(f"Total files in videos/shorts: {total_files}, video_count: {video_count}")
    
    if total_files > video_count:
        files_to_remove = total_files - video_count
        print(f"Removing {files_to_remove} old videos")
        
        # Load all comment folders with their metadata to track which video they belong to
        video_id_to_meta = {}
        for video_id_folder in glob.glob(f"{comments_dir}/*"):
            if os.path.isdir(video_id_folder):
                meta_file = os.path.join(video_id_folder, "meta.json")
                if os.path.exists(meta_file):
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                            video_id_to_meta[meta.get('video_id')] = video_id_folder
                    except:
                        pass
        
        for i in range(files_to_remove):
            try:
                video_file = all_files[i][1]
                filename = os.path.splitext(os.path.basename(video_file))[0]
                
                # Try to find corresponding comment folder and delete it
                for video_id, comment_folder in video_id_to_meta.items():
                    meta_file = os.path.join(comment_folder, "meta.json")
                    if os.path.exists(meta_file):
                        try:
                            with open(meta_file, 'r', encoding='utf-8') as f:
                                meta = json.load(f)
                                # If the title matches, this is the right comment folder
                                if meta.get('title') == filename:
                                    shutil.rmtree(comment_folder)
                                    print(f"Deleted comments for: {filename}")
                                    break
                        except:
                            pass
                
                os.remove(video_file)
                print(f"Deleted old video: {os.path.basename(video_file)}")
                
            except Exception as e:
                print(f"Failed to delete {all_files[i][1]}: {e}")
    else:
        print(f"No cleanup needed")

def save_meta_json(comments_dir, video_info):
    """Save meta.json with basic video information"""
    meta = {
        "video_id": video_info.get('id'),
        "title": video_info.get('title'),
        "channel": video_info.get('channel'),
        "upload_date": video_info.get('upload_date'),
        "duration": video_info.get('duration'),
        "comment_count_estimated": video_info.get('comments'),
        "downloaded_at": int(time.time())
    }
    
    meta_path = os.path.join(comments_dir, "meta.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"Saved meta.json for video {video_info.get('id')}")

def load_index_json(comments_dir):
    """Load existing index.json if it exists"""
    index_path = os.path.join(comments_dir, "index.json")
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Return default index if file doesn't exist
    return {
        "max_top_comments": MAX_COMMENTS,
        "max_replies_per_comment": MAX_REPLIES,
        "top_comments_downloaded": 0,
        "replies_downloaded": 0,
        "has_more_comments": True,
        "next_page_token": None,
        "size_bytes": 0,
        "last_updated": int(time.time())
    }

def save_index_json(comments_dir, index_data):
    """Save index.json with download progress"""
    index_path = os.path.join(comments_dir, "index.json")
    
    # Calculate folder size
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(comments_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    
    index_data["size_bytes"] = total_size
    index_data["last_updated"] = int(time.time())
    
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

def create_comment_structure(comments_dir):
    """Create directory structure for comments"""
    os.makedirs(os.path.join(comments_dir, "top"), exist_ok=True)
    os.makedirs(os.path.join(comments_dir, "replies"), exist_ok=True)

def save_comment(comments_dir, comment_index, comment_data):
    """Save a top-level comment"""
    top_dir = os.path.join(comments_dir, "top")
    comment_file = os.path.join(top_dir, f"c_{comment_index:05d}.json")
    
    with open(comment_file, 'w', encoding='utf-8') as f:
        json.dump(comment_data, f, indent=2, ensure_ascii=False)

def save_reply(comments_dir, comment_index, reply_index, reply_data):
    """Save a reply to a comment"""
    replies_dir = os.path.join(comments_dir, "replies", f"c_{comment_index:05d}")
    os.makedirs(replies_dir, exist_ok=True)
    
    reply_file = os.path.join(replies_dir, f"r_{reply_index:05d}.json")
    
    with open(reply_file, 'w', encoding='utf-8') as f:
        json.dump(reply_data, f, indent=2, ensure_ascii=False)

def download_comments(video_url, video_info, comments_dir, channel_name):
    """Download comments for a video using yt-dlp"""
    if not DOWNLOAD_COMMENTS:
        return
    
    # Check if comments already exist
    top_dir = os.path.join(comments_dir, "top")
    if os.path.exists(top_dir) and len(os.listdir(top_dir)) > 0:
        print(f"Comments already downloaded for: {video_info.get('title')}")
        return
    
    print(f"Downloading comments for: {video_info.get('title')}")
    
    create_comment_structure(comments_dir)
    save_meta_json(comments_dir, video_info)
    
    index_data = load_index_json(comments_dir)
    
    retry_count = 0
    max_retries = 5
    
    try:
        while retry_count < max_retries:
            try:
                # Get comments using yt-dlp's YouTube extractor
                # Note: Use max-comments (with hyphen) to fetch all reply pages
                # Format: max-comments,max-parents,max-replies,max-replies-per-thread
                # Comments have 'parent' field that indicates if they're replies (parent != 'root')
                # Use comment_sort: top to fetch most liked comments (not newest)
                # In Python dict API, use underscores not hyphens for parameter names
                ydl_opts_comments = {
                    "skip_download": True,
                    "quiet": True,
                    "no_warnings": True,
                    "getcomments": True,
                    "extractor_args": {
                        "youtube": {
                            "max-comments": f"{MAX_COMMENTS},all,{MAX_REPLIES},10",
                            "comment-sort": "top"  # Use hyphen in extractor args key
                        }
                    }
                }
                
                with YoutubeDL(ydl_opts_comments) as ydl:
                    video_info_with_comments = ydl.extract_info(video_url, download=False)
                    
                    comments = video_info_with_comments.get('comments', [])
                    
                    if not comments:
                        print(f"No comments available for: {video_info.get('title')}")
                        save_index_json(comments_dir, index_data)
                        return
                    
                    # Separate top-level comments from replies using 'parent' field
                    # Top-level: parent == 'root' or parent is None
                    # Replies: parent == <comment_id>
                    top_level_comments = []
                    replies_by_parent = {}
                    
                    for comment in comments:
                        parent = comment.get('parent', 'root')
                        if parent == 'root' or parent is None:
                            top_level_comments.append(comment)
                        else:
                            if parent not in replies_by_parent:
                                replies_by_parent[parent] = []
                            replies_by_parent[parent].append(comment)
                    
                    # Sort top-level comments by likes (most liked first)
                    top_level_comments.sort(key=lambda x: x.get('like_count', 0), reverse=True)
                    
                    # Limit top-level comments to MAX_COMMENTS
                    top_level_comments = top_level_comments[:MAX_COMMENTS]
                    
                    comment_index = index_data.get("top_comments_downloaded", 0)
                    replies_downloaded = index_data.get("replies_downloaded", 0)
                    
                    for comment in top_level_comments:
                        # Save top-level comment
                        comment_data = {
                            "id": comment.get('id'),
                            "author": comment.get('author'),
                            "timestamp": comment.get('timestamp'),
                            "text": comment.get('text'),
                            "likes": comment.get('like_count', 0)
                        }
                        
                        save_comment(comments_dir, comment_index + 1, comment_data)
                        
                        # Get replies for this comment (limited to MAX_REPLIES)
                        comment_id = comment.get('id')
                        replies = replies_by_parent.get(comment_id, [])[:MAX_REPLIES]
                        
                        for reply_index, reply in enumerate(replies):
                            reply_data = {
                                "id": reply.get('id'),
                                "author": reply.get('author'),
                                "timestamp": reply.get('timestamp'),
                                "text": reply.get('text'),
                                "likes": reply.get('like_count', 0)
                            }
                            
                            save_reply(comments_dir, comment_index + 1, reply_index + 1, reply_data)
                            replies_downloaded += 1
                        
                        comment_index += 1
                    
                    # Update index data
                    index_data["top_comments_downloaded"] = comment_index
                    index_data["replies_downloaded"] = replies_downloaded
                    index_data["has_more_comments"] = len(top_level_comments) >= MAX_COMMENTS
                    
                    save_index_json(comments_dir, index_data)
                    print(f"Downloaded {comment_index} top-level comments with {replies_downloaded} replies")
                    return
                
            except Exception as e:
                retry_count += 1
                print(f"Failed to download comments (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    time.sleep(1)  # Wait before retry
                continue
        
        print(f"Skipping comments after {max_retries} failed attempts")
    
    except Exception as e:
        print(f"Error downloading comments: {e}")
        print(f"Skipping comments for this video")

def download_videos():

    with open("channels.json", "r") as f:
        channels = json.load(f)

    for channel in channels:
        channel_name = channel["channel_name"]
        video_count = channel["video_count"]
        url = f"https://www.youtube.com/@{channel_name}/videos"
        
        # Create directory structure
        videos_dir = f"videos/{channel_name}/videos"
        shorts_dir = f"videos/{channel_name}/shorts"
        comments_dir = f"videos/{channel_name}/comments"
        os.makedirs(videos_dir, exist_ok=True)
        os.makedirs(shorts_dir, exist_ok=True)
        os.makedirs(comments_dir, exist_ok=True)

        # Get already downloaded videos
        downloaded = get_downloaded_videos(videos_dir, shorts_dir)
        print(f"Already downloaded for {channel_name}: {len(downloaded)} videos")

        # Extract playlist info first (without downloading)
        # Fetch more than video_count to account for skipped/failed videos
        ydl_opts_extract = {
            "playlistend": video_count * 5,  # Fetch 5x to handle failures and get enough content
            "quiet": False,  # Show errors for debugging
            "no_warnings": False,
        }
        
        downloaded_count = 0
        entries = []
        
        try:
            with YoutubeDL(ydl_opts_extract) as ydl:
                info = ydl.extract_info(url, download=False)
                entries = info.get("entries", [])
        except (DownloadError, ExtractorError) as e:
            print(f"Warning: Error fetching channel playlist: {str(e)[:100]}")
            print("Continuing with available entries...")
        except Exception as e:
            print(f"Warning: Error fetching channel playlist: {str(e)[:100]}")
            print("Continuing with available entries...")
        
        # Process each entry separately with error handling
        for entry in entries:
            # Stop if we've downloaded enough videos
            if downloaded_count >= video_count:
                break
            
            # Some entries might be None if unavailable
            if not entry:
                continue

            try:
                # Create a fresh YoutubeDL instance for each video to avoid context issues
                ydl_opts_info = {
                    "quiet": True,
                    "no_warnings": True,
                }
                
                with YoutubeDL(ydl_opts_info) as ydl:
                    # Extract full info for each video to get dimensions
                    video_info = ydl.extract_info(entry["webpage_url"], download=False)
                    w = video_info.get('width')
                    h = video_info.get('height')
                    title = video_info.get('title')
                    video_id = video_info.get('id')

                    print(f"{title} [{video_id}] Dimensions: {w} x {h}")

                    # Skip if already downloaded
                    if title in downloaded:
                        print(f"Already downloaded: {title} [{video_id}]")
                        continue

                    # Skip live videos
                    if video_info.get("is_live") or video_info.get("live_status") in ("is_live", "upcoming"):
                        print(f"Skipping live video: {title} [{video_id}]")
                        continue

                    # Determine if it's a short based on aspect ratio
                    is_short = w and h and h > w
                    
                    if is_short:
                        print(f"ITS A SHORTS: {title} [{video_id}]")
                        output_dir = shorts_dir
                    else:
                        output_dir = videos_dir

                    # Download the video to the appropriate folder
                    ytdl_opts_download = {
                        "format": f"bestvideo[height<={QUALITY}]+bestaudio/best[height<={QUALITY}]",
                        "outtmpl": f"{output_dir}/%(title)s [%(id)s].%(ext)s",
                    }
                    
                    with YoutubeDL(ytdl_opts_download) as ydl_download:
                        ydl_download.download([video_info["webpage_url"]])
                    
                    # Verify download was successful by checking if file exists
                    downloaded_file = None
                    for ext in ['.mp4', '.mkv', '.webm', '.mov', '.flv', '.m4a']:
                        potential_file = os.path.join(output_dir, f"{title} [{video_id}]{ext}")
                        if os.path.exists(potential_file):
                            downloaded_file = potential_file
                            break
                    
                    if not downloaded_file:
                        print(f"Warning: Download completed but file not found for: {title}")
                        continue
                    
                    # Verify file is not empty
                    if os.path.getsize(downloaded_file) == 0:
                        print(f"Warning: Downloaded file is empty for: {title}")
                        os.remove(downloaded_file)
                        continue
                    
                    downloaded_count += 1
                    print(f"Downloaded {downloaded_count}/{video_count}: {title} [{video_id}]")
                    
                    # Download comments for this video
                    video_comments_dir = os.path.join(comments_dir, video_id)
                    download_comments(video_info["webpage_url"], video_info, video_comments_dir, channel_name)
                    
            except (DownloadError, ExtractorError) as e:
                error_msg = str(e).lower()
                if "private" in error_msg or "unavailable" in error_msg or "sign in" in error_msg or "empty" in error_msg:
                    print(f"Skipping private/unavailable/empty video")
                else:
                    print(f"Skipping video due to error: {str(e)[:100]}")
                # Continue to next video on any error
                continue
            except Exception as e:
                print(f"Skipping video due to error: {str(e)[:100]}")
                # Continue to next video on any error
                continue
        
        # Clean up old videos to maintain deque behavior
        cleanup_old_videos(videos_dir, shorts_dir, video_count, comments_dir)
        print(f"Completed {channel_name}: Downloaded {downloaded_count}/{video_count} videos")

def main():
    download_videos()

if __name__ == "__main__":
    main()
