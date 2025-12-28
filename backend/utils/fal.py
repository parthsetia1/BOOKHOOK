import os
import requests

FAL_API_KEY = os.getenv("FAL_API_KEY")

def generate_scene(prompt: str):
    url = "https://api.fal.ai/fal-ai/animatediff"
    headers = {"Authorization": f"Key {FAL_API_KEY}"}

    payload = {"prompt": prompt}

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()["video_url"]
