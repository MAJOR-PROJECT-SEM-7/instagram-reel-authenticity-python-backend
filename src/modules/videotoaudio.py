import whisper
import os
from typing import Optional
from audio_extract import extract_audio


def video_to_audio(video_path: str) -> Optional[str]:
    # Check if video path is absolute or relative
    if video_path.startswith("/"):
        video_path = os.path.join(os.getcwd(), video_path[1:])  # Remove leading slash
    else:
        video_path = os.path.join(os.getcwd(), video_path)
    
    # Extract the video filename without extension
    video_filename = os.path.basename(video_path)
    video_name = os.path.splitext(video_filename)[0]
    
    # Create the output audio path
    audio_path = os.path.join("audios", f"{video_name}.mp3")
    
    # Ensure the audios directory exists
    os.makedirs("audios", exist_ok=True)
    
    # Check if audio already exists
    if os.path.exists(audio_path):
        # print(f"Audio file already exists at: {audio_path}")
        return audio_path
    
    # Check if the video file exists
    if not os.path.exists(video_path):
        # print(f"Error: Video file not found at path: {video_path}")
        return None
    
    # Use audio_extract to extract audio from video
    try:
        extract_audio(input_path=video_path, output_path=audio_path)
        return audio_path
    except Exception as e:
        # print(f"Error extracting audio: {str(e)}")
        return None

def audio_to_text(audio_path: str) -> str:
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, task="translate")
    return result["text"]

def video_to_text(video_path: str) -> Optional[str]:
    audio_path = video_to_audio(video_path)
    if audio_path:
        text = audio_to_text(audio_path)
        return text
    return None 
