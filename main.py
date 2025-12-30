import os
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import fal_client
from storage3.utils import StorageException

# -----------------------------------------------------------
# ENV VARIABLES
# -----------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
FAL_KEY = os.getenv("FAL_KEY")

print("FAL KEY:", os.getenv("FAL_KEY"))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------------------------------------
# FASTAPI APP + CORS
# -----------------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# -----------------------------------------------------------
# UTILS
# -----------------------------------------------------------
VIDEO_LENGTH_MAP = {
    "5": "5s",
    "10": "10s",
    "20": "20s",
    "30": "30s",
    "60": "60s",
    "90": "90s"
}

# -----------------------------------------------------------
# ROOT
# -----------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "BookTrailer AI backend running"}


# -----------------------------------------------------------
# CREATE PROJECT
# -----------------------------------------------------------
@app.get("/projects")
def get_projects():
    result = supabase.table("projects").select("*").order("created_at", desc=True).execute()
    return result.data

@app.post("/create_project")
def create_project(
    title: str = Form(...),
    duration: int = Form(...),
    user_id: str = Form(...),
    description: str = Form("")   # make optional with default ""
):

    response = supabase.table("projects").insert({
        "title": title,
        "description": description,
        "status": "created",
        "duration": duration,
        "user_id": user_id
    }).execute()

    return {"project_id": response.data[0]["id"]}


# -----------------------------------------------------------
# GET ALL PROJECTS FOR DASHBOARD
# -----------------------------------------------------------
@app.get("/projects")
def get_projects(user_id: str):
    res = supabase.table("projects").select("*").eq("user_id", user_id).execute()
    return res.data


# -----------------------------------------------------------
# UPLOAD ASSET (IMAGE or DIALOGUE)
# -----------------------------------------------------------
@app.post("/upload_asset")
async def upload_asset(
    project_id: str = Form(...),
    type: str = Form(...),
    dialogue: str = Form(None),
    file: UploadFile = File(None)
):
    file_url = None

    # If an image file is included → upload to Supabase Storage
    if file:
        filename = file.filename
        content = await file.read()
        path = f"{project_id}/{filename}"

        try:
            upload_res = supabase.storage.from_("assets").upload(
                path=path,
                file=content,
                file_options={"content-type": file.content_type}
            )

            file_url = supabase.storage.from_("assets").get_public_url(path)

        except StorageException as e:
            return {"error": "Upload failed", "details": str(e)}

    # Now store asset record
    db_res = supabase.table("assets").insert({
        "project_id": project_id,
        "type": type,
        "file_url": file_url,
        "dialogue": dialogue
    }).execute()

    return {
        "asset_id": db_res.data[0]["id"],
        "file_url": file_url,
        "dialogue": dialogue
    }


# -----------------------------------------------------------
# GENERATE TRAILER (AI IMAGE TO VIDEO)
# -----------------------------------------------------------
@app.post("/generate_trailer")
def generate_trailer(
    project_id: str = Form(...),
    duration: str = Form("10")
):

    # Fetch assets
    assets = supabase.table("assets").select("*").eq("project_id", project_id).execute().data

    images = [a["file_url"] for a in assets if a["type"] == "image" and a["file_url"]]
    dialogues = [a["dialogue"] for a in assets if a["type"] == "dialogue" and a["dialogue"]]

    prompt = " ".join(dialogues) if dialogues else "cinematic dramatic fantasy book trailer"

    VIDEO_LENGTH_MAP = {
        "5": 5,
        "10": 10,
        "20": 20,
        "30": 30,
        "60": 60,
        "90": 90,
    }

    video_length = VIDEO_LENGTH_MAP.get(duration, 10)

    # Auto-generate image if none were uploaded
    if len(images) == 0:
        img_gen = fal_client.submit(
            "fal-ai/flux-pro/v1.1",
            arguments={
                "prompt": prompt,
                "num_inference_steps": 30,
                "guidance_scale": 3.5,
                "size": "768x768"
            }
        ).get()

        images.append(img_gen["images"][0]["url"])

    # Generate book trailer video
    video_task = fal_client.submit(
        "fal-ai/flux-pro/v1.1",
        arguments={
            "prompt": prompt,
            "image_url": images[0],
            "duration": video_length
        }
    )

    result = video_task.get()

    video_url = result["video"]["url"]

    # Save in DB
    supabase.table("projects").update({
        "status": "completed",
        "video_url": video_url
    }).eq("id", project_id).execute()

    return {
        "status": "completed",
        "video_url": video_url,
        "duration": duration
    }
