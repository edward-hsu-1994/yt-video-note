import asyncio
import os
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from src.agents.video_screenshot_time_picker import VideoScreenshotTimePicker
from src.agents.video_summit_note import VideoSummitNote
from src.transcriber import Transcriber
from src.ui import display_video_info
from src.video_screenshot import VideoScreenshot
from src.yt_downloader import YtDownloader


async def main():
    console = Console()
    yt_downloader = YtDownloader()
    video_screenshot = VideoScreenshot()
    transcriber = Transcriber()
    video_summit_note = VideoSummitNote()
    video_screenshot_time_picker = VideoScreenshotTimePicker()

    console.print("YT Video Note", style="bold red")
    console.rule()
    console.print("Please enter a YouTube URL: ", style="yellow", end="")

    url = input().strip()
    console.rule()

    console.print(f"Extract video info...")

    video_info = {}
    # Hidden yt-dlp logging
    with open(os.devnull, 'w') as devnull:
        with redirect_stdout(devnull), redirect_stderr(devnull):
            video_info = await yt_downloader.extract_info(url)

    await display_video_info(console, video_info)

    console.print(f"Download video...")
    os.makedirs("./results", exist_ok=True)
    os.makedirs(f"./results/{video_info["id"]}", exist_ok=True)
    video_path = f"./results/{video_info["id"]}/video.mp4"

    if os.path.exists(video_path):
        console.print(f"Video already downloaded. Skipping download.", style="yellow")
    else:
        await yt_downloader.download(url, video_path)
        console.print("Video downloaded successfully.", style="green")


    console.print(f"Transcribe video...")
    transcribe_path = f"./results/{video_info['id']}/transcription.txt"

    transcribe = ""
    if os.path.exists(transcribe_path):
        console.print(f"Transcription already exists. Skipping transcription.", style="yellow")

        with open(transcribe_path, 'r', encoding='utf-8') as f:
            transcribe = f.read()
            console.print(f"Transcription loaded from {transcribe_path}", style="green")
    else:
        transcribe = await transcriber.transcribe_with_timestamps_str(video_path)
        with open(transcribe_path, 'w', encoding='utf-8') as f:
            f.write(transcribe)
            console.print(f"Transcription saved to {transcribe_path}", style="green")

    console.print(f"Generate video summary...")
    summary_content = ""
    if os.path.exists(f"./results/{video_info['id']}/summary-raw.md"):
        console.print("Video summary already exists. Skipping summary generation.", style="yellow")
        with open(f"./results/{video_info['id']}/summary-raw.md", 'r', encoding='utf-8') as f:
            summary_content = f.read()
    else:
        summary_content = await video_summit_note.summarize(video_info, transcribe)
        summary_path = f"./results/{video_info['id']}/summary-raw.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        console.print(f"Video summary saved to {summary_path}", style="green")

    console.print(f"Select screenshot times...")
    images = {}
    if os.path.exists(f"./results/{video_info['id']}/screenshots"):
        console.print("Screenshots already exist. Skipping screenshot selection.", style="yellow")
        # list all image in screenshots folder
        folder = Path(f"./results/{video_info['id']}/screenshots")
        for file in folder.iterdir():
            if file.is_file() and file.suffix.lower() in ['.jpg']:
                key = file.stem  # filename without extension
                image_binary = None
                with open(file, 'rb') as f:
                    image_binary = f.read()
                images[key] = image_binary

        console.print(f"Found {len(images)} existing screenshots.", style="green")
    else:
        screenshot_times = await video_screenshot_time_picker.select_times(video_info, summary_content, transcribe)
        console.print(f"Video processing complete.", style="green")

        for time in screenshot_times:
            image_binary = await video_screenshot.get_image(video_path, time)
            images[time] = image_binary
            image_path = f"./results/{video_info['id']}/screenshots/{time}.jpg"
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, 'wb') as f:
                f.write(image_binary)

        console.print(f"Saved {len(images)} screenshots.", style="green")

    console.print(f"Enhancing summary generation...")
    summary_content = await video_summit_note.enhance_summarize(summary_content, transcribe, images)
    with open(f"./results/{video_info['id']}/summary.md", 'w', encoding='utf-8') as f:
        f.write(summary_content)
    console.print(f"Summary saved to ./results/{video_info['id']}/summary.md", style="green")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
