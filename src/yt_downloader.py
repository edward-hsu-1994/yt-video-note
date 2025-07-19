import os
import shutil
from typing import Dict, Any

import aiohttp
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

    async def download_subtitle(self, url: str, lang: str) -> str:
        ydl_opts = {
            'skip_download': True,
            'subtitleslangs': [lang],
            'subtitlesformat': 'srt',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            subtitles = info.get('subtitles')
            if not subtitles or lang not in subtitles:
                return None

            all_format_subtitles = subtitles[lang]
            srt_url = None

            for subtitle_format in all_format_subtitles:
                if subtitle_format['ext'].lower() == 'srt':
                    srt_url = subtitle_format['url']
                    break

            if not srt_url:
                return None

            # async download file
            async with aiohttp.ClientSession() as session:
                async with session.get(srt_url) as response:
                    return await response.text()