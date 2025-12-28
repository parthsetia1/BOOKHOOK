from fastapi import FastAPI, Form, UploadFile
from utils.supabase import get_supabase
from utils.fal import generate_scene
from utils.video import merge_videos
import uuid

app = FastAPI()
supabase = get_supabase()

@app.post("/create_project")
def create_project(title: str = Form(...),
                   description: str = Form(...),
                   duration: int = Form(...),
                   user_id: str = Form(...)):

    res = supabase.table("projects").insert({
        "title": title,
        "description": description,
        "duration": duration,
        "user_id": user_id
    }).execute()

    return {"project_id": res.data[0]["id"]}


@app.post("/upload_asset")
async def upload_asset(project_id: str = Form(...),
                       type: str = Form(...),
                       dialogue: str = Form(""),
                       file: UploadFile = None):

    file_url = None

    if file:
        contents = await file.read()
        path = f"{project_id}/{uuid.uuid4()}-{file.filename}"

        supabase.storage.from_("assets").upload(path, contents)
        file_url = supabase.storage.from_("assets").get_public_url(path)

    supabase.table("assets").insert({
        "project_id": project_id,
        "type": type,
        "file_url": file_url,
        "dialogue": dialogue
    }).execute()

    return {"status": "ok"}


@app.post("/generate_trailer")
def generate_trailer(project_id: str = Form(...)):

    # Get assets
    assets = supabase.table("assets").select("*").eq("project_id", project_id).execute().data

    video_urls = []

    # Generate video for each dialogue/image
    for a in assets:
        prompt = a["dialogue"] or "cinematic scene from storybook"
        video_url = generate_scene(prompt)
        video_urls.append(video_url)

    # Merge into one video
    output = merge_videos(video_urls)

    # Upload final video
    file_path = f"{project_id}-final.mp4"
    with open(output, "rb") as f:
        supabase.storage.from_("videos").upload(file_path, f.read())

    public_url = supabase.storage.from_("videos").get_public_url(file_path)

    # Update DB
    supabase.table("projects").update({
        "status": "completed",
        "video_url": public_url
    }).eq("id", project_id).execute()

    return {"video_url": public_url}
