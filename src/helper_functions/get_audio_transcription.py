import os
import whisper
import asyncio
from functools import partial

async def audio_to_text(audio_path: str, model: whisper.Whisper) -> str:
    if audio_path.startswith("/reels/audio/"):
        filename = os.path.basename(audio_path)
        audio_path = os.path.join(os.path.dirname(__file__), "../../reels/audio", filename)
        audio_path = os.path.normpath(audio_path)
    
    loop = asyncio.get_running_loop()
    # Run the blocking transcription in a separate thread
    result = await loop.run_in_executor(None, partial(model.transcribe, audio_path, task="translate"))
    return result["text"]