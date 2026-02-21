from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import cloudinary
import cloudinary.uploader
import cloudinary.utils
import json
import os

app = FastAPI()

# CORS (if using different domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 ENV VARIABLES (set in Render)
CLOUD_NAME = os.getenv("CLOUD_NAME")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ADMIN_KEY = os.getenv("ADMIN_KEY", "Dhvanit")
APP_USER = os.getenv("APP_USER", "patelkanostudent@gmail.com")
APP_PASS = os.getenv("APP_PASS", "Dhvanit")




cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET
)

DB_FILE = "videos_db.json"

# serve static
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return RedirectResponse("/static/login.html")

# ---------------- DB ----------------
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return []

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# ---------------- LOGIN ----------------
from pydantic import BaseModel

class LoginData(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: LoginData):
    if data.username == APP_USER and data.password == APP_PASS:
        return {"status": "success"}
    return {"status": "fail"}

# ---------------- UPLOAD ----------------
@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    x_admin_key: str = Header(None)
):
    # 🔐 check admin key
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

    result = cloudinary.uploader.upload(file.file, resource_type="video")

    video_url = result["secure_url"]
    public_id = result["public_id"]

    thumbnails = []
    for t in [1, 3, 5]:
        thumb_url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type="video",
            format="jpg",
            transformation=[
                {"width": 400, "height": 225, "crop": "fill"},
                {"start_offset": str(t)}
            ]
        )
        thumbnails.append(thumb_url)

    videos = load_db()
    videos.append({
        "title": file.filename,
        "url": video_url,
        "thumbnails": thumbnails
    })
    save_db(videos)

    return {"message": "Uploaded"}

# ---------------- GET VIDEOS ----------------
@app.get("/videos")
def get_videos():
    return load_db()