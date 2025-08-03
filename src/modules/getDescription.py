import os
import json
from pathlib import Path
from typing import Dict, Any
from core.config import settings

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class VideoAnalysis(BaseModel):
    """Structured output model for video analysis"""
    visual_analysis: str = Field(description="Detailed description of what is happening visually in the video - scenes, actions, expressions, transitions, colors, objects, people, etc.")
    audio_analysis: str = Field(description="Comprehensive audio analysis including the exact words spoken by the speaker each and every word, background sounds, music, speech content, tone, detailed transcription of any spoken words, who said what to whom")
    meaning: str = Field(description="The main message, purpose, or meaning that the video creator is trying to convey or communicate to the audience")


def generate_description_from_video(video_url: str) -> Dict[str, Any]:
    """Generate structured video analysis using LangChain and Google Gemini AI"""
    try:
        # Validate input
        if not video_url:
            raise ValueError("videoUrl is required")
        
        # Convert URL to local file path
        if video_url.startswith("/"):
            video_path = Path.cwd() / video_url[1:]  # Remove leading slash
        else:
            video_path = Path.cwd() / video_url
        
        # Check if video file exists
        if not video_path.exists():
            raise FileNotFoundError("Video file not found")
        
        print(f"Generating structured analysis for: {video_path}")
        
        # Initialize Google API key
        google_api_key = settings.GOOGLE_API_KEY
        if not google_api_key:
            raise ValueError("Google API key not configured")
        
        # Initialize LangChain ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=google_api_key,
            temperature=0.1,  # Lower temperature for more consistent structured output
        )
        
        # Set up JSON output parser
        parser = JsonOutputParser(pydantic_object=VideoAnalysis)
        
        # Create the prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("human", """
Analyze the attached video thoroughly and provide a comprehensive structured analysis in JSON format.

{format_instructions}

Focus on these three key areas:

1. **Visual Analysis**: Describe in detail what is happening visually in the video:
   - Key scenes and visual elements
   - Actions and movements
   - People's expressions and body language
   - Visual transitions and cuts
   - Colors, lighting, and composition
   - Any on-screen text, captions, or graphics
   - Objects, settings, and environments

2. **Audio Analysis**: Provide comprehensive audio analysis:
   - Background sounds and ambient noise
   - Music and sound effects
   - Speech content with detailed transcription
   - Who is speaking and to whom
   - Tone of voice and emotional delivery
   - Volume levels and audio quality
   - Any audio cues or emphasis

3. **Meaning**: Explain the core message and purpose:
   - What is the video creator trying to convey?
   - What is the main message or theme?
   - What emotions or reactions is it meant to evoke?
   - What are the key facts, claims, or information presented?
   - What is the intended audience and purpose?

Provide detailed, specific observations rather than generic descriptions. Be thorough and analytical.
            """)
        ])
        
        # Read video file
        with open(video_path, 'rb') as video_file:
            video_buffer = video_file.read()
        
        # Determine MIME type based on file extension
        file_extension = video_path.suffix.lower()
        mime_type_map = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".mkv": "video/x-matroska",
        }
        mime_type = mime_type_map.get(file_extension, "video/mp4")
        
        # Create the message with video content
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
        
        # Generate response using LangChain
        response = llm.invoke([message])
        
        # Parse the JSON response
        try:
            parsed_analysis = parser.parse(response.content)
        except Exception as parse_error:
            print(f"JSON parsing error: {parse_error}")
            # Fallback: try to extract JSON from response
            try:
                # Look for JSON in the response content
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    parsed_analysis = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
            except:
                # Final fallback: create structured response from text
                parsed_analysis = {
                    "visual_analysis": "Unable to parse structured visual analysis from response",
                    "audio_analysis": "Unable to parse structured audio analysis from response", 
                    "meaning": "Unable to parse structured meaning from response",
                    "raw_response": response.content
                }
        
        print("Structured analysis generated successfully")
        
        # Return successful response with structured data
        return {
            "success": True,
            "videoUrl": video_url,
            "analysis": parsed_analysis,
            "fileSize": f"{len(video_buffer) / (1024 * 1024):.2f} MB",
            "mimeType": mime_type,
        }
        
    except Exception as error:
        print(f"Error in VideoAnalysis: {error}")
        
        # Handle specific error types
        if isinstance(error, FileNotFoundError) or (hasattr(error, 'errno') and error.errno == 2):
            raise ValueError("Video file not found")
        
        if "API key" in str(error):
            raise ValueError("Invalid or missing Google API key")
        
        if "quota" in str(error).lower() or "limit" in str(error).lower():
            raise ValueError("API quota exceeded. Please try again later.")
        
        # Generic error response
        raise ValueError(f"Failed to generate video analysis: {str(error)}")


# Alternative function with chain approach
def generate_video_analysis_with_chain(video_url: str) -> Dict[str, Any]:
    """Alternative implementation using LangChain chain approach"""
    try:
        # Validate input and setup (same as above)
        if not video_url:
            raise ValueError("videoUrl is required")
        
        if video_url.startswith("/"):
            video_path = Path.cwd() / video_url[1:]
        else:
            video_path = Path.cwd() / video_url
        
        if not video_path.exists():
            raise FileNotFoundError("Video file not found")
        
        # Initialize LangChain components
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
        )
        
        parser = JsonOutputParser(pydantic_object=VideoAnalysis)
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("human", """
Analyze this video and provide structured JSON output with these exact fields:
- visual_analysis: Detailed visual description
- audio_analysis: Comprehensive audio analysis with transcription
- meaning: Main message the creator wants to convey

{format_instructions}

Be thorough and specific in your analysis.
            """)
        ])
        
        # Create the chain
        chain = prompt | llm | parser
        
        # Read and process video
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
        
        # Note: This approach might need adjustment based on how your LangChain version handles media
        # You might need to pass the video data differently depending on the implementation
        
        print("Generating analysis with chain approach...")
        
        # For now, this would need to be adapted based on how your LangChain setup handles video input
        # The exact implementation may vary depending on the LangChain version and Google integration
        
        result = chain.invoke({
            "format_instructions": parser.get_format_instructions(),
            # Video handling would need to be implemented based on your LangChain setup
        })
        
        return {
            "success": True,
            "videoUrl": video_url,
            "analysis": result,
            "fileSize": f"{len(video_buffer) / (1024 * 1024):.2f} MB",
            "mimeType": mime_type,
        }
        
    except Exception as error:
        print(f"Error in chain-based analysis: {error}")
        raise ValueError(f"Failed to generate video analysis: {str(error)}")