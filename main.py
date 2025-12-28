from fastapi import FastAPI, Form, UploadFile
from utils.supabase import insert, select, upload_file
import requests
import uuid
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FAL_API_KEY = os.getenv("FAL_API_KEY")

@app.post("/create_project")
def create_project(title: str = Form(...),
                   description: str = Form(...),
                   duration: int = Form(...),
                   user_id: str = Form(...)):
    
    res = insert("projects", {
        "title": title,
        "description": description,
        "duration": duration,
        "user_id": user_id
    })
    return {"project_id": res[0]["id"]}

@app.post("/upload_asset")
async def upload_asset(project_id: str = Form(...),
                       type: str = Form(...),
                       dialogue: str = Form(""),
                       file: UploadFile = None):

    file_url = None

    if file:
        contents = await file.read()
        path = f"{project_id}/{uuid.uuid4()}-{file.filename}"
        file_url = upload_file("assets", path, contents)

    insert("assets", {
        "project_id": project_id,
        "type": type,
        "file_url": file_url,
        "dialogue": dialogue
    })

    return {"status": "ok"}

@app.post("/generate_trailer")
def generate_trailer(project_id: str = Form(...)):
    
    assets = select("assets", f"id, dialogue, file_url&project_id=eq.{project_id}")
    scenes = [a["dialogue"] for a in assets if a["dialogue"]]

    prompt = "Create a cinematic book trailer with scenes:\n"
    for i, s in enumerate(scenes): prompt += f"Scene {i+1}: {s}\n"

    response = requests.post(
        "https://api.fal.ai/fal-ai/story-video",
        json={"prompt": prompt},
        headers={"Authorization": f"Key {FAL_API_KEY}"}
    )

    video_url = response.json()["video_url"]

    video_data = requests.get(video_url).content
    final_name = f"{project_id}-trailer.mp4"
    public_url = upload_file("videos", final_name, video_data)

    insert("projects", {
        "id": project_id,
        "status": "completed",
        "video_url": public_url
    })

    return {"video_url": public_url}
