import os
import whisper

def audio_to_text(audio_path: str) -> str:
    if audio_path.startswith("/reels/audio/"):
        filename = os.path.basename(audio_path)
        audio_path = os.path.join(os.path.dirname(__file__), "../../reels/audio", filename)
        audio_path = os.path.normpath(audio_path)
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, task="translate")
    return result["text"]