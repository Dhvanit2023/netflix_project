from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cloudinary
import cloudinary.uploader
import cloudinary.utils
import json
import os

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- CONFIG ----------------
CLOUD_NAME = os.getenv("CLOUD_NAME")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ADMIN_KEY = os.getenv("ADMIN_KEY")
APP_USER = os.getenv("APP_USER")
APP_PASS = os.getenv("APP_PASS")
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

# ---------------- CLOUDINARY ----------------
cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET
)

# ---------------- FILES ----------------
VIDEO_DB = "videos_db.json"
AD_DB = "ads_db.json"

# ---------------- STATIC ----------------
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return RedirectResponse("/static/login.html")

# ---------------- DB FUNCTIONS ----------------
def load_db(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def save_db(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# ---------------- LOGIN ----------------
class LoginData(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: LoginData):

    # ADMIN LOGIN
    if data.username == ADMIN_USER and data.password == ADMIN_PASS:
        return {
            "status": "success",
            "role": "admin",
            "plan": "premium"
        }

    # USER LOGIN → PREMIUM
    if data.username == APP_USER and data.password == APP_PASS:
        return {
            "status": "success",
            "role": "user",
            "plan": "premium"
        }

    return {"status": "fail"}
# ---------------- UPLOAD VIDEO ----------------
@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    x_admin_key: str = Header(None)
):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Upload to Cloudinary
    result = cloudinary.uploader.upload(file.file, resource_type="video")

    video_url = result["secure_url"]
    public_id = result["public_id"]

    # Generate thumbnails
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

    # Save to DB
    videos = load_db(VIDEO_DB)
    videos.append({
        "title": file.filename,
        "url": video_url,
        "thumbnails": thumbnails
    })
    save_db(VIDEO_DB, videos)

    return {"message": "Video Uploaded"}

# ---------------- GET VIDEOS ----------------
@app.get("/videos")
def get_videos():
    return load_db(VIDEO_DB)

# ---------------- UPLOAD AD ----------------
@app.post("/upload_ad")
async def upload_ad(
    file: UploadFile = File(...),
    x_admin_key: str = Header(None)
):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

    result = cloudinary.uploader.upload(file.file, resource_type="video")

    ad_url = result["secure_url"]

    ads = load_db(AD_DB)
    ads.append(ad_url)
    save_db(AD_DB, ads)

    return {"message": "Ad Uploaded"}

# ---------------- GET ADS ----------------
@app.get("/ads")
def get_ads():
    return load_db(AD_DB)
