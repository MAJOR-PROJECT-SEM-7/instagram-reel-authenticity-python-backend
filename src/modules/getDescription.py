import os
from pathlib import Path
from core.config import settings
import google.generativeai as genai


def generate_description_from_video(video_url):
    """Generate video description using Google Gemini AI"""
    try:
        # Validate input
        if not video_url:
            raise ValueError("videoUrl is required")
        
        # Convert URL to local file path
        # Assuming videoUrl is like "/reels/filename.mp4" or "reels/filename.mp4"
        if video_url.startswith("/"):
            video_path = Path.cwd() / video_url[1:]  # Remove leading slash
        else:
            video_path = Path.cwd() / video_url
        
        # Check if video file exists
        if not video_path.exists():
            raise FileNotFoundError("Video file not found")
        
        print(f"Generating description for: {video_path}")
        
        # Initialize Google Gemini model
        google_api_key = settings.GOOGLE_API_KEY
        if not google_api_key:
            raise ValueError("Google API key not configured")
        
        # Configure the Gemini API
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
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
        
        # Create prompt for the generation request
        prompt = """
        Analyze the attached video and give me a single, focused description. 
        • Concentrate on audio: background sounds, music, speech content, tone.  
        • Concentrate on visuals: key scenes, actions, expressions, transitions.  
        • Note any on-screen text: captions, graphics, timestamps.  
        • Highlight the core facts or claims made.  
        Do NOT include any opening or closing pleasantries—just the raw, descriptive summary.
        """.strip()
        
        # Create video part for the API
        video_part = {
            "mime_type": mime_type,
            "data": video_buffer
        }
        
        # Generate content
        print("Generating video description...")
        response = model.generate_content([prompt, video_part])
        
        print("Description generated successfully")
        
        # Return successful response
        return {
            "success": True,
            "videoUrl": video_url,
            "description": response.text,
            "fileSize": f"{len(video_buffer) / (1024 * 1024):.2f} MB",
            "mimeType": mime_type,
        }
        
    except Exception as error:
        print(f"Error in VideoDescription: {error}")
        
        # Handle specific error types
        if isinstance(error, FileNotFoundError) or (hasattr(error, 'errno') and error.errno == 2):
            raise ValueError("Video file not found")
        
        if "API key" in str(error):
            raise ValueError("Invalid or missing Google API key")
        
        if "quota" in str(error).lower() or "limit" in str(error).lower():
            raise ValueError("API quota exceeded. Please try again later.")
        
        # Generic error response
        raise ValueError("Failed to generate video description")
