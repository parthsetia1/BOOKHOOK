import requests
import uuid
from moviepy.editor import VideoFileClip, concatenate_videoclips

def download(url):
    filename = f"{uuid.uuid4()}.mp4"
    r = requests.get(url)

    with open(filename, "wb") as f:
        f.write(r.content)

    return filename


def merge_videos(video_urls, output="final.mp4"):
    clips = []

    for url in video_urls:
        path = download(url)
        clips.append(VideoFileClip(path))

    final = concatenate_videoclips(clips)
    final.write_videofile(output, fps=24)

    return output
