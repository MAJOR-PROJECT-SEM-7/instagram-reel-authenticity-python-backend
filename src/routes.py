from fastapi import APIRouter
from src.modules.getLinkFromUrl import get_link_from_url
from src.modules.downloadAndCompress import download_and_compress_video
from src.modules.getDescription import generate_description_from_video
from src.modules.process_reel import process_reel
from src.modules.video_check_classifier import get_video_check_info
from src.modules.notWorthyResponse import not_worthy_response
from src.websearchengine.pipeline import pipeline

router = APIRouter()

@router.get("/getLink")
async def get_link_endpoint(url: str):
    return get_link_from_url(url)

@router.post("/downloadAndCompress")
async def download_and_compress_endpoint(request_data: dict):
    url = request_data.get("url")
    filename = request_data.get("filename")
    return download_and_compress_video(url, filename)

@router.post("/videoDescription")
async def video_description_endpoint(request_data: dict):
    video_url = request_data.get("videoUrl")
    return generate_description_from_video(video_url)

@router.post("/videoCheck")
async def video_check_endpoint(request_data: dict):
    description = request_data.get("description")
    return get_video_check_info(description)

@router.post("/notWorthyResponse")
async def not_worthy_response_endpoint(request_data: dict):
    description = request_data.get("description")
    category = request_data.get("category")
    return not_worthy_response(description, category)

@router.post("/processReel")
async def process_reel_endpoint(request_data: dict):
    url = request_data.get("url")
    return process_reel(url)



@router.post("/webSearch")
async def search_endpoint(request_data: dict):
    query = request_data.get("query")
    return pipeline(query)