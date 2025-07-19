import os
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field


class VideoScreenshotTimes(BaseModel):
    timestamps: list[float] = Field(description="Timestamps of key moments in the video that best represent its content, in seconds")
class VideoScreenshotTimePicker:
    def __init__(self):
        llm = ChatOpenAI(model=os.environ.get("TIME_PICKER_MODEL", "gpt-4.1"))

        self.agent = create_react_agent(
            model=llm,
            prompt="""
            You are a professional content analyst. Based on the provided summary and video transcript, 
            identify specific timestamps or time ranges in the video where taking screenshots would most 
            enhance or supplement the summary. For each suggested timestamp, briefly explain why the 
            visual from that moment would be valuable in reinforcing or clarifying the summary content. 
            """,
            tools=[],
            response_format=VideoScreenshotTimes
        )
        pass

    async def select_times(self, video_info: dict[str,Any] ,video_summary: str, transcribe_with_timestamp: str) -> list[float]:
        video_info_str = "Video Information:\n```\n"
        for key, value in video_info.items():
            video_info_str += f"{key}: {value}\n"
        video_info_str += "```\n"

        state = {
            "messages": [
                HumanMessage(video_info_str),
                HumanMessage(
f"""Video Summary:
```
{video_summary}
```                
"""),
                HumanMessage(
f"""
Transcription with Timestamps:
```
{transcribe_with_timestamp}
```
""")
            ]
        }

        response = await self.agent.ainvoke(state)

        timestamps: VideoScreenshotTimes = response.get("structured_response")

        return timestamps.timestamps