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


@app.post("/upload_asset")
async def upload_asset(
    project_id: str = Form(...),
    type: str = Form(...),
    dialogue: str = Form(None),
    file: UploadFile = File(None),
):
    response = supabase.table("assets").insert({
        "project_id": project_id,
        "type": type,
        "file_url": None,
        "dialogue": dialogue
    }).execute()

    if not response.data:
        return {"error": "Insert failed"}

    return {"asset_id": response.data[0]["id"]}


@app.post("/generate_trailer")
def generate_trailer(project_id: str = Form(...)):
    # placeholder response to avoid 404
    return {"status": "processing"}
