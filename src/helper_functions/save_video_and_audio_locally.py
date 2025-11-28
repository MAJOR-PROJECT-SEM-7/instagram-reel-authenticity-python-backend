import os
import ffmpeg
from audio_extract import extract_audio
import subprocess
import httpx
from pathlib import Path
import asyncio
from functools import partial

ROOT_DIR = Path.cwd() / "reels"
VIDEO_DIR = ROOT_DIR / "video"
AUDIO_DIR = ROOT_DIR / "audio"

for d in [ROOT_DIR, VIDEO_DIR, AUDIO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def check_ffmpeg_installation() -> bool:
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

async def save_video_and_audio_locally(url: str, filename: str, log: bool = False):
    try:
        if not url or not filename:
            return {"success": False}

        # Check if video and audio already exist
        video_path = VIDEO_DIR / filename
        video_name = os.path.splitext(filename)[0]
        audio_path = AUDIO_DIR / f"{video_name}.mp3"
        
        if video_path.exists() and audio_path.exists():
            if log:
                print("Video and audio already exist, skipping download and processing")
            video_url = f"/reels/video/{filename}"
            audio_filename = f"{video_name}.mp3"
            audio_url = f"/reels/audio/{audio_filename}"
            return {
                "success": True,
                "video": video_url,
                "audio": audio_url
            }

        if log:
            print("Downloading video")
        video_path = await download_reel(url, filename)
        if log:
            if video_path:
                print("Video downloaded")
            else:
                print("Failed to download video")
        
        if not video_path:
            return {"success": False}

        if log:
            print("Converting video to audio")
        
        # Run audio extraction in executor
        loop = asyncio.get_running_loop()
        audio_path_str = await loop.run_in_executor(None, video_to_audio, video_path)
        
        if not audio_path_str:
            return {"success": False}

        if log:
            print("Compressing video")
        
        # Run compression in executor
        compressed_video_path = await loop.run_in_executor(None, compress_reel, video_path)
        
        if log:
            if compressed_video_path:
                print("Video compressed")
            else:
                print("Failed to compress video")
        if not compressed_video_path:
            return {"success": False}
        
        video_url = f"/reels/video/{filename}"
        audio_filename = os.path.basename(audio_path_str)
        audio_url = f"/reels/audio/{audio_filename}"

        return {
            "success": True,
            "video": video_url,
            "audio": audio_url
        }
    except Exception:
        return {"success": False}

async def download_reel(url: str, filename: str) -> str:
    try:
        file_path = VIDEO_DIR / filename
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url, headers=headers, timeout=30.0) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as writer:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        writer.write(chunk)
        return str(file_path)
    except Exception:
        return None

def compress_reel(video_path: str) -> str:
    try:
        input_path = Path(video_path)
        temp_path = VIDEO_DIR / f"temp_{input_path.name}"

        if not input_path.exists():
            return None

        original_size = input_path.stat().st_size / (1024 * 1024)
        if original_size <= 2:
            return str(input_path)

        if not check_ffmpeg_installation():
            return str(input_path)

        try:
            (
                ffmpeg
                .input(str(input_path))
                .output(
                    str(temp_path),
                    vcodec='libx264',
                    preset='fast',
                    crf=28,
                    maxrate='1M',
                    bufsize='2M',
                    acodec='aac',
                    audio_bitrate='128k',
                    movflags='+faststart',
                    vf='scale=720:-2'
                )
                .overwrite_output()
                .run(capture_stdout=True, quiet=True)
            )
        except ffmpeg.Error:
            return None

        input_path.unlink()
        temp_path.rename(input_path)
        return str(input_path)
    except Exception:
        temp_path = VIDEO_DIR / f"temp_{Path(video_path).name}"
        if temp_path.exists():
            temp_path.unlink()
        return None

def video_to_audio(video_path: str) -> str:
    try:
        video_filename = os.path.basename(video_path)
        video_name = os.path.splitext(video_filename)[0]
        audio_path = AUDIO_DIR / f"{video_name}.mp3"
        if audio_path.exists():
            return str(audio_path)
        if not os.path.exists(video_path):
            return None
        extract_audio(input_path=video_path, output_path=str(audio_path))
        return str(audio_path)
    except Exception:
        return None
