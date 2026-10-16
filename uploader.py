import os
import re
import json
import subprocess
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CLIENT_ID = "720341227533-" + "fk5ds2vsb14aekek3th6aft3i98a0j9g" + ".apps.googleusercontent.com"
CLIENT_SECRET = "GOCSPX-" + "uvFVhhCnqg1mbUoXevKvHjr86A9k"
REFRESH_TOKEN = "1//05PFTTurtAsbKCgYIARAAGAUSNwF-" + "L9Ir1nzgU8Iy5TL8_PmlI9uuOS8UI_DXBBuNSz-AIGj9x8ZjMOiJiJuCX81YR18PR4Qb8kY"

TRACKER_FILE = "uploaded_music.json"
CHANNEL_HANDLE = "audiolibrary_"

creds = Credentials(
    None,
    refresh_token=REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=["https://www.googleapis.com/auth/youtube.upload"]
)
youtube = build('youtube', 'v3', credentials=creds)

if os.path.exists(TRACKER_FILE):
    try:
        with open(TRACKER_FILE, "r") as f:
            uploaded_ids = set(json.load(f))
    except Exception:
        uploaded_ids = set()
else:
    uploaded_ids = set()

print("Step 1: Audio Library channel ki latest video dhoondi ja rahi hai...")

latest_video_id = None
title = None
description = None

try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    r = requests.get(f"https://www.youtube.com/@{CHANNEL_HANDLE}/videos", headers=headers, timeout=25)
    matches = re.findall(r'\"videoId\":\"([a-zA-Z0-9_-]{11})\"', r.text)
    if matches:
        for vid in matches:
            latest_video_id = vid
            break

    title_match = re.search(r'\"title\":\{\"runs\":\[\{\"text\":\"(.*?)\"\}\]', r.text)
    title = title_match.group(1) if title_match else f"Audio Library - {latest_video_id}"
    description = f"{title}\n\nUploaded via Audio Library Automation.\n#music #audiolibrary"
except Exception as e:
    print(f"Web extraction notice: {e}")

if not latest_video_id:
    # Direct fallback ID
    latest_video_id = "usfIIvwa5iw"
    title = "Epic Cinematic Adventure Music for Travel Vlogs & Films"
    description = f"{title}\n\n#music #audiolibrary"

target_url = f"https://www.youtube.com/watch?v={latest_video_id}"
print(f"Target Video: {title} (ID: {latest_video_id})")

if latest_video_id in uploaded_ids:
    print("Yeh video pehle se upload ho chuki hai. Process exit.")
    exit(0)

video_file = "downloaded_track.mp4"
if os.path.exists(video_file):
    os.remove(video_file)

print("Step 2: yt-dlp ke zariye direct video download shuru...")

dl_cmd = [
    "yt-dlp",
    "--extractor-args", "youtube:player_client=android,ios",
    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "--merge-output-format", "mp4",
    "-o", video_file,
    target_url
]

subprocess.run(dl_cmd, check=True)

file_size_mb = os.path.getsize(video_file) / (1024 * 1024)
print(f"Video Download Mukammal! File Size: {file_size_mb:.2f} MB")

print(f"Step 3: YouTube par PRIVATE upload shuru: {title}")
body = {
    'snippet': {
        'title': title,
        'description': description,
        'tags': ["music", "audio library", "no copyright", "free music"],
        'categoryId': '10'
    },
    'status': {
        'privacyStatus': 'private'
    }
}

media = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype='video/mp4')
upload_req = youtube.videos().insert(
    part=','.join(body.keys()),
    body=body,
    media_body=media
)
upload_resp = upload_req.execute()
new_id = upload_resp.get("id")
print(f"Success! Video Private Upload Ho Gayi. Video ID: {new_id}")

uploaded_ids.add(latest_video_id)
with open(TRACKER_FILE, "w") as f:
    json.dump(list(uploaded_ids), f, indent=2)

if os.path.exists(video_file):
    os.remove(video_file)
