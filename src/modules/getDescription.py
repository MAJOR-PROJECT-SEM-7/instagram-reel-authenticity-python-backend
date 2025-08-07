import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from core.config import settings

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class VideoClaim(BaseModel):
    claim: str = Field(
        description=(
            "A specific factual statement or implication from the video. "
            "This could be something explicitly said, or something shown/implied — "
            "such as an event, action, or allegation about a public figure or entity."
        )
    )
    evidence: str = Field(
        description=(
            "What visual or verbal content supports this claim in the video? "
            "Summarize the exact supporting context shown or stated."
        )
    )
    is_worth_verifying: bool = Field(
        description=(
            "Is this claim significant enough to verify? "
            "That includes anything potentially misleading, controversial, false, or viral — "
            "especially if it could influence public opinion or spread misinformation."
        )
    )

class VideoAnalysis(BaseModel):
    category: str = Field(description="Type of video - e.g., meme, educational, vlog, news, etc.")
    claims: List[VideoClaim] = Field(description="List of key claims made in the video, with evidence and a verification flag")
    is_worthy: bool = Field(description="Whether the overall video is worth verifying")
    why_not_worthy: Optional[str] = Field(description="If not worthy, explain why. Else, null")

def generate_description_from_video(video_url: str, transcript: Optional[str] = None) -> Dict[str, Any]:
    try:
        if not video_url:
            raise ValueError("videoUrl is required")

        if video_url.startswith("/"):
            video_path = Path.cwd() / video_url[1:]
        else:
            video_path = Path.cwd() / video_url

        if not video_path.exists():
            raise FileNotFoundError("Video file not found")

        print(f"Generating structured analysis for: {video_path}")
        if transcript:
            print("Using provided transcript to enhance analysis")

        google_api_key = settings.GOOGLE_API_KEY
        if not google_api_key:
            raise ValueError("Google API key not configured")

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=google_api_key,
            temperature=0.1,
        )

        parser = JsonOutputParser(pydantic_object=VideoAnalysis)

        base_prompt = """
You are an expert fact-checking analyst.

Your job is to analyze a short video and provide structured data.

{format_instructions}

Tasks:
1. Classify the video category (e.g., meme, educational, vlog, political, etc.).
2. Determine whether the video is worthy of checking:
    - If it contains health, political, scientific, or potentially misleading claims, set is_worthy to true.
    - If it's just humor, entertainment, or doesn't contain any factual claims, set is_worthy to false and explain why in why_not_worthy.

3. If is_worthy is true, extract each major claim made:
    - claim: The specific message or assertion.
    - evidence: What in the video supports it? (captions, speech, visuals)
    - is_worth_verifying: Whether it seems controversial, exaggerated, or false enough to need checking.
"""

        if transcript:
            transcript_section = f"""

Use the transcript below to understand context. Do not include it in your final response.
```
{transcript}
```
"""
            full_prompt = base_prompt + transcript_section
        else:
            full_prompt = base_prompt

        prompt_template = ChatPromptTemplate.from_messages([
            ("human", full_prompt)
        ])

        with open(video_path, 'rb') as video_file:
            video_buffer = video_file.read()

        file_extension = video_path.suffix.lower()
        mime_type_map = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".mkv": "video/x-matroska",
        }
        mime_type = mime_type_map.get(file_extension, "video/mp4")

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": prompt_template.format_messages(
                        format_instructions=parser.get_format_instructions()
                    )[0].content
                },
                {
                    "type": "media",
                    "mime_type": mime_type,
                    "data": video_buffer
                }
            ]
        )

        print("Generating structured video analysis...")

        response = llm.invoke([message])

        try:
            parsed_analysis = parser.parse(response.content)
        except Exception as parse_error:
            print(f"JSON parsing error: {parse_error}")
            try:
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    parsed_analysis = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
            except:
                parsed_analysis = {
                    "category": "Unknown",
                    "claims": [],
                    "is_worthy": False,
                    "why_not_worthy": "Unable to parse structured analysis.",
                    "raw_response": response.content
                }

        print("Structured analysis generated successfully")

        response_data = {
            "success": True,
            "videoUrl": video_url,
            "analysis": parsed_analysis,
            "fileSize": f"{len(video_buffer) / (1024 * 1024):.2f} MB",
            "mimeType": mime_type,
        }

        if transcript:
            response_data["transcriptProvided"] = True
            response_data["transcriptLength"] = len(transcript)
        else:
            response_data["transcriptProvided"] = False

        return response_data

    except Exception as error:
        print(f"Error in VideoAnalysis: {error}")

        if isinstance(error, FileNotFoundError) or (hasattr(error, 'errno') and error.errno == 2):
            raise ValueError("Video file not found")

        if "API key" in str(error):
            raise ValueError("Invalid or missing Google API key")

        if "quota" in str(error).lower() or "limit" in str(error).lower():
            raise ValueError("API quota exceeded. Please try again later.")

        raise ValueError(f"Failed to generate video analysis: {str(error)}")
