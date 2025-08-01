from fastapi import APIRouter
from src.modules.getLinkFromUrl import get_link_from_url
from src.modules.downloadAndCompress import download_and_compress_video
from src.modules.getDescription import generate_description_from_video
from src.modules.process_reel import process_reel

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

@router.post("/processReel")
async def process_reel_endpoint(request_data: dict):
    url = request_data.get("url")
    return process_reel(url)