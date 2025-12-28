from fastapi import FastAPI, Form
from utils.supabase import get_supabase
import requests
import uuid
import os

FAL_API_KEY = os.getenv("FAL_API_KEY")

app = FastAPI()
supabase = get_supabase()

@app.post("/generate_trailer")
def generate_trailer(project_id: str = Form(...)):
    # Get assets
    assets = supabase.table("assets").select("*").eq("project_id", project_id).execute().data

    # Merge all dialogues into a list
    scenes = [a["dialogue"] for a in assets if a["dialogue"]]

    # Build prompt for multi-scene trailer
    prompt = "Create a cinematic animated book trailer with the following scenes:\n"
    for i, scene in enumerate(scenes):
        prompt += f"Scene {i+1}: {scene}\n"

    # Call Fal.ai story generator model
    response = requests.post(
        "https://api.fal.ai/fal-ai/story-video",
        json={"prompt": prompt},
        headers={"Authorization": f"Key {FAL_API_KEY}"}
    )

    result = response.json()
    video_url = result["video_url"]

    # Download and upload to Supabase
    video_data = requests.get(video_url).content
    file_path = f"{project_id}-trailer.mp4"
    supabase.storage.from_("videos").upload(file_path, video_data)
    public_url = supabase.storage.from_("videos").get_public_url(file_path)

    # Update DB
    supabase.table("projects").update({
        "status": "completed",
        "video_url": public_url
    }).eq("id", project_id).execute()

    return {"video_url": public_url}
