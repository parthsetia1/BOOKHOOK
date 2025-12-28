import requests
import uuid
import ffmpeg

def download_video(url):
    filename = f"{uuid.uuid4()}.mp4"
    r = requests.get(url)
    with open(filename, "wb") as f:
        f.write(r.content)
    return filename

def merge_videos(video_urls, output="final.mp4"):
    # Download all videos
    downloaded = [download_video(url) for url in video_urls]

    # Create input streams
    inputs = [ffmpeg.input(video) for video in downloaded]

    # Concatenate them
    ffmpeg.concat(*inputs, v=1, a=1).output(output).run(overwrite_output=True)

    return output
