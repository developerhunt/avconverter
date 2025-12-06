from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import shutil
import uuid

app = FastAPI()

# --- CORS SETTINGS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CLEANUP FUNCTION ---
def remove_file(path: str):
    try:
        if os.path.exists(path):
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
    session_id = str(uuid.uuid4())
    
    # 1. Detect Extensions safely
    img_ext = os.path.splitext(image.filename)[1].lower() or ".jpg"
    aud_ext = os.path.splitext(audio.filename)[1].lower() or ".mp3"

    img_path = f"input_{session_id}{img_ext}"
    aud_path = f"input_{session_id}{aud_ext}"
    vid_path = f"output_{session_id}.mp4"

    try:
        # 2. Save Files
        with open(img_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        with open(aud_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # 3. FFmpeg Command (Optimized for 512MB RAM)
        # -vf "scale=1280:-2" -> Resizes video to 720p width, auto height
        # This prevents the server from crashing due to low memory
        command = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img_path,
            "-i", aud_path,
            "-vf", "scale=1280:-2",   # <--- THE CRITICAL FIX
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-b:a", "128k",           # Lower audio bitrate slightly to save buffer
            "-pix_fmt", "yuv420p",
            "-shortest",
            vid_path
        ]
        
        # Run subprocess
        subprocess.run(command, check=True)

        # 4. Schedule Cleanup
        background_tasks.add_task(remove_file, img_path)
        background_tasks.add_task(remove_file, aud_path)
        background_tasks.add_task(remove_file, vid_path)

        return FileResponse(vid_path, media_type="video/mp4", filename="Rendered_Video.mp4")

    except Exception as e:
        # Cleanup on error
        if os.path.exists(img_path): os.remove(img_path)
        if os.path.exists(aud_path): os.remove(aud_path)
        print(f"Error: {e}")
        return {"error": str(e)}
