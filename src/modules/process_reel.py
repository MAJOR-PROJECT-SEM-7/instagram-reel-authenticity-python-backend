import time
from src.modules.getLinkFromUrl import get_link_from_url
from src.modules.downloadAndCompress import download_and_compress_video
from src.modules.getDescription import generate_description_from_video
from src.modules.video_check_classifier import get_video_check_info
from src.modules.notWorthyResponse import not_worthy_response
from src.modules.videotoaudio import video_to_text

def process_reel(url):
    start_time = time.time()
    
    link: dict = get_link_from_url(url)
    print(f"Get link time: {time.time() - start_time:.2f} seconds")
    
    saved_link = download_and_compress_video(link["videoUrl"], link["filename"])
    print(f"Download and compress time: {time.time() - start_time:.2f} seconds")
    
    audio_transcript = video_to_text(saved_link)
    print(f"Audio transcription time: {time.time() - start_time:.2f} seconds")
    
    description = generate_description_from_video(saved_link, audio_transcript)
    print(f"Generate description time: {time.time() - start_time:.2f} seconds")
    
    
    description["audioTranscript"] = audio_transcript
    description["category"] = description.get("category")
    description["isWorthChecking"] = description.get("is_worth_verifying")
    
    if not description.get("isWorthChecking"):
        not_worthy_result = not_worthy_response(description.get("analysis"), description.get("category"))
        description["notWorthyResponse"] = not_worthy_result
        print(f"Not worthy response time: {time.time() - start_time:.2f} seconds")
    
    print(f"Total processing time: {time.time() - start_time:.2f} seconds")
    return description