from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import shutil
import uuid

app = FastAPI()

# --- CORS SETTINGS ---
# This allows your GitHub Pages (Frontend) to talk to this Render (Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- CLEANUP FUNCTION ---
def remove_file(path: str):
    """Deletes temporary files after the response is sent"""
    try:
        os.remove(path)
    except Exception as e:
        print(f"Error deleting file {path}: {e}")

@app.get("/")
def home():
    return {"status": "System Operational", "engine": "FFmpeg Native"}

@app.post("/render")
async def render_video(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...), 
    audio: UploadFile = File(...)
):
    # 1. Generate Unique Session ID
    # This prevents users from overwriting each other's files
    session_id = str(uuid.uuid4())
    img_path = f"input_{session_id}.jpg"
    aud_path = f"input_{session_id}.mp3"
    vid_path = f"output_{session_id}.mp4"

    try:
        # 2. Save Uploaded Files to Server Disk
        with open(img_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        with open(aud_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # 3. Execute FFmpeg Command (Native Linux Speed)
        # -preset ultrafast: Trades compression efficiency for max speed
        # -tune stillimage: Optimizes specifically for image+audio
        command = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img_path,
            "-i", aud_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            vid_path
        ]
        
        # Run subprocess (Wait for it to finish)
        subprocess.run(command, check=True)

        # 4. Schedule Cleanup
        # These run AFTER the return statement sends the file
        background_tasks.add_task(remove_file, img_path)
        background_tasks.add_task(remove_file, aud_path)
        background_tasks.add_task(remove_file, vid_path)

        # 5. Return Video
        return FileResponse(vid_path, media_type="video/mp4", filename="Rendered_Video.mp4")

    except Exception as e:
        # Cleanup if error occurs
        if os.path.exists(img_path): os.remove(img_path)
        if os.path.exists(aud_path): os.remove(aud_path)
        return {"error": str(e)}
