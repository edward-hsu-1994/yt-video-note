from typing import Dict, Any

import yt_dlp


class YtDownloader:
    def __init__(self):
        pass

    async def extract_info(self, url:str)->Dict[str, Any]:
        ydl_opts = {}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            return info_dict


    async def download(self, url: str, output_path: str = None):
        ydl_opts = {
            'format': 'bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4][height<=480]',
            'outtmpl': output_path,
            'merge_output_format': 'mp4'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])