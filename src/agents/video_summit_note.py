import base64
import os
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from pydantic.fields import Field


class SummitNoteOutput(BaseModel):
    markdown: str = Field(description="Markdown summary of the video")

class VideoSummitNote:
    def __init__(self):
        llm = ChatOpenAI(model=os.environ.get("SUMMIT_NOTE_MODEL", "gpt-4.1"))

        self.agent = create_react_agent(
            model=llm,
            prompt="""
            You are a professional video summarizer who creates concise, 
            informative markdown summaries that capture the key insights, 
            main points, and essential context of the video.
            
            You don't need to emphasize in your content that this is a summary of the video.
            """,
            tools=[],
            response_format=SummitNoteOutput
        )

        self.enhance_agent = create_react_agent(
            model=llm,
            prompt="""
            Based on the original summary content, extend and enrich it by incorporating 
            information from the video transcript and appropriately selected user-provided 
            images. Evaluate each image to determine its relevance and value before including 
            it in the Markdown summary. There is no need to mention that the content is 
            enhanced or expanded. You may insert images only within the content, not in the 
            headings. If the summary includes bullet points, do not place images at the 
            beginning of a bullet point; instead, insert them on a new line within the list.
            
            Please select appropriate images in suitable places and insert them using Markdown syntax.
            """,
            tools=[],
            response_format=SummitNoteOutput
        )
        pass

    async def summarize(self, video_info: dict[str,Any], transcribe_with_timestamp: str ) -> str:
        video_info_str = "Video Information:\n```\n"
        for key, value in video_info.items():
            video_info_str += f"{key}: {value}\n"
        video_info_str += "```\n"

        state = {
            "messages": [
                HumanMessage(video_info_str),
                HumanMessage(transcribe_with_timestamp)
            ]
        }

        response = await self.agent.ainvoke(state)

        summit_note:SummitNoteOutput = response.get("structured_response")

        return summit_note.markdown

    async def enhance_summarize(self, exists_summary: str, transcribe_with_timestamp:str, images: dict[str,Any]) -> str:
        image_message = []
        for key, value in images.items():
            image_message.append(
                HumanMessage(content=[
                    {
                        "type": "text",
                        "text": f"Timestamp: {key}s, FilePath: `./screenshots/{key}.jpg`"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64.b64encode(value).decode('utf-8')}"
                        }
                    }
                ])
            )

        state = {
            "messages": [
                HumanMessage(
f"""
Existing Summary:
```
{exists_summary}
```
"""),
                *image_message
            ]
        }


        response = await self.enhance_agent.ainvoke(state)

        summit_note:SummitNoteOutput = response.get("structured_response")

        return summit_note.markdown