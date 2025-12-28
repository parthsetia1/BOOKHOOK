import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json"
}

def insert(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    return requests.post(url, json=data, headers=headers).json()

def select(table, query="*"):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select={query}"
    return requests.get(url, headers=headers).json()

def upload_file(bucket, path, file_bytes):
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{path}"
    h = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/octet-stream"
    }
    res = requests.put(url, headers=h, data=file_bytes)
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"
