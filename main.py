from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from supabase.client import create_client
import os

app = FastAPI()

# ⭐ CORS MUST BE IMMEDIATELY AFTER app INITIALIZATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # allow ALL origins (frontend included)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⭐ ENV VARIABLES
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/create_project")
async def create_project(
    title: str = Form(...),
    description: str = Form(...),
    duration: int = Form(...),
    user_id: str = Form(...),
):
    # Insert
    result = supabase.table("projects").insert({
        "title": title,
        "description": description,
        "duration": duration,
        "user_id": user_id,
        "status": "created"
    }).execute()

    if result.error:
        return {"error": result.error.message}

    project_id = result.data[0]["id"]

    return {"project_id": project_id}

@app.get("/")
def root():
    return {"message": "Backend is running"}
