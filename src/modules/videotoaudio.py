import whisper
import os
import subprocess


def video_to_audio(video_path):
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
        print(f"Audio file already exists at: {audio_path}")
        return audio_path
    
    # Check if the video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at path: {video_path}")
        return None
    
    # Use ffmpeg to extract audio from video with more robust error handling
    try:
        # Use simpler ffmpeg command without -map option
        result = subprocess.run(
            ["ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", audio_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return audio_path
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e}")
        print(f"STDERR: {e.stderr}")
        # Try alternative approach if first method fails
        try:
            result = subprocess.run(
                ["ffmpeg", "-i", video_path, "-vn", audio_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return audio_path
        except subprocess.CalledProcessError as e2:
            print(f"Second attempt failed: {e2}")
            print(f"STDERR: {e2.stderr}")
            return None
    except Exception as e:
        print(f"Unexpected error during audio extraction: {str(e)}")
        return None

def audio_to_text(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, task="translate")
    return result["text"]

def video_to_text(video_path):
    audio_path = video_to_audio(video_path)
    if audio_path:
        text = audio_to_text(audio_path)
        return {"text": text}
    return {"error": "Failed to extract audio from video"}
