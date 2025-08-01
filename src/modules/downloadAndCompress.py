import subprocess
import requests
from pathlib import Path
import ffmpeg


# Ensure reels directory exists
reels_dir = Path.cwd() / "reels"
reels_dir.mkdir(parents=True, exist_ok=True)


def check_ffmpeg_installation():
    """Function to check if ffmpeg is installed"""
    try:
        # Try to get ffmpeg version
        subprocess.run(["ffmpeg", "-version"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FFmpeg is not installed or not in PATH. Please install FFmpeg: https://ffmpeg.org/download.html")
        return False


def download_and_compress_video(url, filename):
    """Main function to download and compress video"""
    try:
        if not url or not filename:
            raise ValueError("URL and filename are required")
        
        download_reel(url, filename)
        
        # Check if ffmpeg is installed before attempting compression
        if not check_ffmpeg_installation():
            print("FFmpeg not found. Skipping compression and returning uncompressed video.")
            return f"/reels/{filename}"
        
        compress_reel(filename)
        return f"/reels/{filename}"
        
    except Exception as error:
        print(f"Error in ReelDownloadandCompressor: {error}")
        raise ValueError("Failed to download and compress reel")


def download_reel(url, filename):
    """Download video file from URL"""
    try:
        file_path = reels_dir / filename
        
        # Download the video file
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, 
                              stream=True, 
                              timeout=30,  # 30 second timeout
                              headers=headers)
        response.raise_for_status()
        
        # Write to file
        with open(file_path, 'wb') as writer:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    writer.write(chunk)
        
        print(f"Reel downloaded successfully: {file_path}")
        return str(file_path)
        
    except Exception as error:
        print(f"Error downloading reel: {error}")
        raise ValueError(f"Failed to download reel: {str(error)}")


def compress_reel(filename):
    """Compress video file using ffmpeg"""
    try:
        input_path = reels_dir / filename
        temp_path = reels_dir / f"temp_{filename}"
        
        # Check if file exists
        if not input_path.exists():
            raise ValueError(f"File not found: {input_path}")
        
        # Get original file size
        original_size = input_path.stat().st_size / (1024 * 1024)  # Size in MB
        print(f"Original file size: {original_size:.2f} MB")
        
        # If file is already under 2MB, return as is
        if original_size <= 2:
            print("File is already under 2MB, no compression needed")
            return str(input_path)
        
        # Compress video using ffmpeg-python
        try:
            print("FFmpeg compression started")
            
            # First compression attempt
            (
                ffmpeg
                .input(str(input_path))
                .output(str(temp_path),
                       vcodec='libx264',
                       preset='fast',
                       crf=28,
                       maxrate='1M',
                       bufsize='2M',
                       acodec='aac',
                       audio_bitrate='128k',
                       movflags='+faststart',
                       vf='scale=720:-2')
                .overwrite_output()
                .run(capture_stdout=True, check=True)
            )
            
            print("Compression finished successfully")
            
        except ffmpeg.Error as e:
            print(f"FFmpeg error: {e}")
            raise ValueError(f"Compression failed: {str(e)}")
        
        # Check compressed file size
        compressed_size = temp_path.stat().st_size / (1024 * 1024)
        print(f"Compressed file size: {compressed_size:.2f} MB")
        
        # If still too large, try more aggressive compression
        if compressed_size > 3:
            print("File still too large, applying more aggressive compression...")
            
            final_temp_path = reels_dir / f"final_temp_{filename}"
            
            try:
                (
                    ffmpeg
                    .input(str(temp_path))
                    .output(str(final_temp_path),
                           vcodec='libx264',
                           preset='fast',
                           crf=32,  # Higher CRF for more compression
                           maxrate='800k',  # Lower max bitrate
                           bufsize='1600k',
                           acodec='aac',
                           audio_bitrate='96k',  # Lower audio bitrate
                           movflags='+faststart',
                           vf='scale=640:-2')  # Scale to 640p width
                    .overwrite_output()
                    .run(capture_stdout=True, check=True)
                )
                
                # Remove intermediate temp file
                temp_path.unlink()
                # Move final temp to temp path
                final_temp_path.rename(temp_path)
                
            except ffmpeg.Error as e:
                raise ValueError(f"Second compression failed: {str(e)}")
            
            final_size = temp_path.stat().st_size / (1024 * 1024)
            print(f"Final compressed file size: {final_size:.2f} MB")
        
        # Replace original file with compressed version
        input_path.unlink()
        temp_path.rename(input_path)
        
        print(f"Reel compressed successfully: {input_path}")
        return f"reels/{filename}"
        
    except Exception as error:
        # Clean up temp files if they exist
        temp_path = reels_dir / f"temp_{filename}"
        final_temp_path = reels_dir / f"final_temp_{filename}"
        
        if temp_path.exists():
            temp_path.unlink()
        if final_temp_path.exists():
            final_temp_path.unlink()
        
        print(f"Error compressing reel: {error}")
        raise ValueError(f"Failed to compress reel: {str(error)}")


# Alternative implementation using subprocess instead of ffmpeg-python
def compress_reel_subprocess(filename):
    """Alternative compression method using subprocess (if ffmpeg-python is not available)"""
    try:
        input_path = reels_dir / filename
        temp_path = reels_dir / f"temp_{filename}"
        
        # Check if file exists
        if not input_path.exists():
            raise ValueError(f"File not found: {input_path}")
        
        # Get original file size
        original_size = input_path.stat().st_size / (1024 * 1024)  # Size in MB
        print(f"Original file size: {original_size:.2f} MB")
        
        # If file is already under 2MB, return as is
        if original_size <= 2:
            print("File is already under 2MB, no compression needed")
            return str(input_path)
        
        # First compression attempt
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '28',
            '-maxrate', '1M',
            '-bufsize', '2M',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-vf', 'scale=720:-2',
            '-y', str(temp_path)
        ]
        
        print("FFmpeg compression started")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            raise ValueError(f"Compression failed: {result.stderr}")
        
        print("Compression finished successfully")
        
        # Check compressed file size
        compressed_size = temp_path.stat().st_size / (1024 * 1024)
        print(f"Compressed file size: {compressed_size:.2f} MB")
        
        # If still too large, try more aggressive compression
        if compressed_size > 3:
            print("File still too large, applying more aggressive compression...")
            
            final_temp_path = reels_dir / f"final_temp_{filename}"
            
            cmd2 = [
                'ffmpeg', '-i', str(temp_path),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '32',
                '-maxrate', '800k',
                '-bufsize', '1600k',
                '-c:a', 'aac',
                '-b:a', '96k',
                '-movflags', '+faststart',
                '-vf', 'scale=640:-2',
                '-y', str(final_temp_path)
            ]
            
            result2 = subprocess.run(cmd2, capture_output=True, text=True)
            
            if result2.returncode != 0:
                raise ValueError(f"Second compression failed: {result2.stderr}")
            
            # Remove intermediate temp file
            temp_path.unlink()
            # Move final temp to temp path
            final_temp_path.rename(temp_path)
            
            final_size = temp_path.stat().st_size / (1024 * 1024)
            print(f"Final compressed file size: {final_size:.2f} MB")
        
        # Replace original file with compressed version
        input_path.unlink()
        temp_path.rename(input_path)
        
        print(f"Reel compressed successfully: {input_path}")
        return f"reels/{filename}"
        
    except Exception as error:
        # Clean up temp files if they exist
        temp_path = reels_dir / f"temp_{filename}"
        final_temp_path = reels_dir / f"final_temp_{filename}"
        
        if temp_path.exists():
            temp_path.unlink()
        if final_temp_path.exists():
            final_temp_path.unlink()
        
        print(f"Error compressing reel: {error}")
        raise ValueError(f"Failed to compress reel: {str(error)}")


# Example usage:
if __name__ == "__main__":
    # Example usage
    # url = "https://example.com/video.mp4"
    # filename = "example_video.mp4"
    # result = download_and_compress_video(url, filename)
    # print(f"Video processed: {result}")
    pass