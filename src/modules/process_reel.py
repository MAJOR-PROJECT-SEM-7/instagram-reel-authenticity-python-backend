from src.modules.getLinkFromUrl import get_link_from_url
from src.modules.downloadAndCompress import download_and_compress_video
from src.modules.getDescription import generate_description_from_video
from src.modules.video_check_classifier import get_video_check_info
from src.modules.notWorthyResponse import not_worthy_response

def process_reel(url):
    link: dict = get_link_from_url(url)
    saved_link = download_and_compress_video(link["videoUrl"], link["filename"])
    description = generate_description_from_video(saved_link)
    check_info = get_video_check_info(description.get("analysis"))
    description["category"] = check_info.get("category")
    description["isWorthChecking"] = check_info.get("isWorthChecking")
    if not check_info.get("isWorthChecking"):
        not_worthy_result = not_worthy_response(description.get("analysis"), description.get("category"))
        description["notWorthyResponse"] = not_worthy_result
    return description