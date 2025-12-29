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
from fastapi import Form

@app.post("/generate_trailer")
def generate_trailer(project_id: str = Form(...)):
    # 1. Fetch project assets
    assets = supabase.table("assets").select("*").eq("project_id", project_id).execute().data

    images = [a["file_url"] for a in assets if a["type"] == "image" and a["file_url"]]
    dialogues = [a["dialogue"] for a in assets if a["type"] == "dialogue" and a["dialogue"]]

    if len(images) == 0:
        return {"error": "No images uploaded"}

    prompt = " ".join(dialogues) if dialogues else "cinematic dramatic book trailer"

    # 2. Use new Fal API syntax (v3+)
    runner = fal_client.submit(
        "fal-ai/image-to-video",
        arguments={
            "prompt": prompt,
            "image_url": images[0],
            "video_length": "10s"
        }
    )

    # 3. Wait for result
    result = runner.get()
    video_url = result["video"]["url"]

    # 4. Save result in Supabase
    supabase.table("projects").update({
        "status": "completed",
        "video_url": video_url
    }).eq("id", project_id).execute()

    return {"video_url": video_url, "status": "completed"}
