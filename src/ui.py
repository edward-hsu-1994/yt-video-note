from typing import Any
from rich.console import Console
from rich.table import Table


async def display_video_info(console: Console, video_info: dict[str,Any]):
    video_info_table = Table(show_header=True, header_style="bold magenta", title="Video Information")
    video_info_table.add_column("Key")
    video_info_table.add_column("Value")

    for key in ["id","webpage_url", "title", "channel", "thumbnail", "description", "categories", "duration", "view_count", "like_count"]:
        if key in video_info and video_info[key] is not None:
            video_info_table.add_row(key, str(video_info[key]))

    console.print(video_info_table)