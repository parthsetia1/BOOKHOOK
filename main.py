from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/")
def root():
    return {"message": "Backend is running"}


@app.post("/create_project")
def create_project(
    title: str = Form(...),
    description: str = Form(...),
    duration: int = Form(...),
    user_id: str = Form(...)
):
    response = supabase.table("projects").insert({
        "title": title,
        "description": description,
        "duration": duration,
        "user_id": user_id,
        "status": "created"
    }).execute()

    if not response.data:
        return {"error": "Insert failed"}

    return {"project_id": response.data[0]["id"]}


from fastapi import UploadFile, File, Form
from storage3.utils import StorageException

@app.post("/upload_asset")
async def upload_asset(
    project_id: str = Form(...),
    type: str = Form(...),
    dialogue: str = Form(None),
    file: UploadFile = File(None)
):
    file_url = None

    if file is not None:
        filename = file.filename
        content = await file.read()
        path = f"{project_id}/{filename}"

        try:
            # correct upload method for supabase-py v2
            upload_res = supabase.storage.from_("assets").upload(
                path=path,
                file=content,   # raw bytes
                file_options={
                    "content-type": file.content_type
                }
            )

            # Now get public URL
            file_url = supabase.storage.from_("assets").get_public_url(path)

        except StorageException as e:
            return {
                "error": "Storage Upload Failed",
                "details": str(e),
                "path": path
            }

    # Insert into "assets" table
    response = supabase.table("assets").insert({
        "project_id": project_id,
        "type": type,
        "file_url": file_url,
        "dialogue": dialogue
    }).execute()

    return {
        "asset_id": response.data[0]["id"],
        "file_url": file_url,
        "dialogue": dialogue
    }





import fal_client
import time
from fastapi import Form

@app.post("/generate_trailer")
def generate_trailer(project_id: str = Form(...)):
    # 1. Fetch all assets for project
    asset_res = supabase.table("assets").select("*").eq("project_id", project_id).execute()

    images = []
    dialogues = []

    for a in asset_res.data:
        if a["type"] == "image" and a["file_url"]:
            images.append(a["file_url"])
        if a["type"] == "dialogue" and a["dialogue"]:
            dialogues.append(a["dialogue"])

    if not images:
        return {"error": "No images uploaded yet"}

    # 2. Create a joined prompt from dialogues
    final_prompt = " ".join(dialogues) if dialogues else "dramatic fantasy cinematic trailer"

    # 3. Call Fal AI Image-to-Video model
    runner = fal_client.submit(
        "fal-ai/image-to-video",
        arguments={
            "prompt": final_prompt,
            "video_length": "10s",
            "image_url": images[0]  # <-- IMPORTANT: Fal accepts one image
        },
        api_key=os.getenv("FAL_API_KEY")
    )

    # 4. Wait for Fal result
    result = runner.get()
    video_url = result["video"]["url"]

    # 5. Save video URL into Supabase
    supabase.table("projects").update({
        "status": "completed",
        "video_url": video_url
    }).eq("id", project_id).execute()

    return {
        "status": "completed",
        "video_url": video_url
    }

