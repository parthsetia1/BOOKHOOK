from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os

app = FastAPI()

# CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
def root():
    return {"status": "backend running (supabase-v2)"}

@app.post("/create_project")
def create_project(
    title: str = Form(...),
    description: str = Form(...),
    duration: int = Form(...),
    user_id: str = Form(...)
):
    try:
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

    except Exception as e:
        return {"error": str(e)}

