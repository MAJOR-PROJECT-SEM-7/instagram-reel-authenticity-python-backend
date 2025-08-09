import re
import json
import time
import urllib.parse
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup


class HTTPError(Exception):
    def __init__(self, message: str, status: int) -> None:
        super().__init__(message)
        self.status = status


def get_link_from_url(url: str) -> Dict[str, Any]:
    if not url:
        raise ValueError("URL is required")

    validation_error = is_valid_instagram_url(url)
    if validation_error:
        raise ValueError(validation_error)

    try:
        post_id = get_post_id_from_url(url)
        if not post_id:
            raise ValueError("Invalid Post URL - Could not extract ID")

        post_json = get_video_info(post_id)
        post_json['success'] = True
        return post_json
    except Exception as error:
        return {'success': False, 'message': str(error)}


def get_post_id_from_url(post_url: str) -> str:
    share_regex = r"^https://(?:www\.)?instagram\.com/share/([a-zA-Z0-9_-]+)/?.*"
    post_regex = r"^https://(?:www\.)?instagram\.com/p/([a-zA-Z0-9_-]+)/?.*"
    reel_regex = r"^https://(?:www\.)?instagram\.com/reels?/([a-zA-Z0-9_-]+)/?.*"

    if re.match(share_regex, post_url):
        try:
            reel_id = fetch_reel_id_from_share_url(post_url)
            return reel_id
        except Exception as error:
            raise error

    post_match = re.match(post_regex, post_url)
    if post_match and post_match.group(1):
        return post_match.group(1)

    reel_match = re.match(reel_regex, post_url)
    if reel_match and reel_match.group(1):
        return reel_match.group(1)

    raise ValueError("Unable to extract ID from URL")


def fetch_reel_id_from_share_url(share_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(share_url, headers=headers, allow_redirects=True)
        if not response.ok:
            raise ValueError(f"Failed to fetch share URL: {response.status_code}")

        patterns = [
            r"/reel/([a-zA-Z0-9_-]+)",
            r"/p/([a-zA-Z0-9_-]+)",
            r"/reels/([a-zA-Z0-9_-]+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, response.url)
            if match and match.group(1):
                return match.group(1)

        raise ValueError(f"Reel ID not found in redirected URL: {response.url}")
    except Exception as error:
        raise error


def is_valid_instagram_url(post_url: str) -> Optional[str]:
    if not post_url:
        return "Instagram URL was not provided"

    if "instagram.com/" not in post_url:
        return "Invalid URL: does not contain Instagram domain"

    if not post_url.startswith("https://"):
        return 'Invalid URL: should start with "https://"'

    post_regex = r"^https://(?:www\.)?instagram\.com/p/([a-zA-Z0-9_-]+)/?(?:\?.*)?$"
    reel_regex = r"^https://(?:www\.)?instagram\.com/reels?/([a-zA-Z0-9_-]+)/?(?:\?.*)?$"
    share_regex = r"^https://(?:www\.)?instagram\.com/share/([a-zA-Z0-9_-]+)/?(?:\?.*)?$"

    if not (re.match(post_regex, post_url) or
            re.match(reel_regex, post_url) or
            re.match(share_regex, post_url)):
        return "URL does not match Instagram post, reel, or share format"

    return None


def get_ig_video_filename(reel_id: str):
    """Generate filename for video using reel ID"""
    return f"reel_{reel_id}.mp4"


def encode_graphql_request_data(shortcode):
    request_data = {
        "av": "0",
        "__d": "www",
        "__user": "0",
        "__a": "1",
        "__req": "3",
        "__hs": "19624.HYP:instagram_web_pkg.2.1..0.0",
        "dpr": "3",
        "__ccg": "UNKNOWN",
        "__rev": "1008824440",
        "__s": "xf44ne:zhh75g:xr51e7",
        "__hsi": "7282217488877343271",
        "__dyn": "7xeUmwlEnwn8K2WnFw9-2i5U4e0yoW3q32360CEbo1nEhw2nVE4W0om78b87C0yE5ufz81s8hwGwQwoEcE7O2l0Fwqo31w9a9x-0z8-U2zxe2GewGwso88cobEaU2eUlwhEe87q7-0iK2S3qazo7u1xwIw8O321LwTwKG1pg661pwr86C1mwraCg",
        "__csr": "gZ3yFmJkillQvV6ybimnG8AmhqujGbLADgjyEOWz49z9XDlAXBJpC7Wy-vQTSvUGWGh5u8KibG44dBiigrgjDxGjU0150Q0848azk48N09C02IR0go4SaR70r8owyg9pU0V23hwiA0LQczA48S0f-x-27o05NG0fkw",
        "__comet_req": "7",
        "lsd": "AVqbxe3J_YA",
        "jazoest": "2957",
        "__spin_r": "1008824440",
        "__spin_b": "trunk",
        "__spin_t": "1695523385",
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "PolarisPostActionLoadPostQueryQuery",
        "variables": json.dumps({
            "shortcode": shortcode,
            "fetch_comment_count": None,
            "fetch_related_profile_media_count": None,
            "parent_comment_count": None,
            "child_comment_count": None,
            "fetch_like_count": None,
            "fetch_tagged_user_count": None,
            "fetch_preview_comment_count": None,
            "has_threaded_comments": False,
            "hoisted_comment_id": None,
            "hoisted_reply_id": None,
        }),
        "server_timestamps": "true",
        "doc_id": "10015901848480474",
    }
    return urllib.parse.urlencode(request_data)


def format_graphql_json(data, reel_id):
    filename = get_ig_video_filename(reel_id)
    width = str(data["dimensions"]["width"])
    height = str(data["dimensions"]["height"])
    video_url = data["video_url"]

    return {
        "filename": filename,
        "width": width,
        "height": height,
        "videoUrl": video_url,
    }


def format_page_json(post_html, reel_id):
    video_element = post_html.find("meta", {"property": "og:video"})
    if not video_element:
        return None

    video_url = video_element.get("content")
    if not video_url:
        return None

    width_element = post_html.find("meta", {"property": "og:video:width"})
    height_element = post_html.find("meta", {"property": "og:video:height"})

    width = width_element.get("content") if width_element else ""
    height = height_element.get("content") if height_element else ""
    filename = get_ig_video_filename(reel_id)

    return {
        "filename": filename,
        "width": width,
        "height": height,
        "videoUrl": video_url,
    }


def get_video_json_from_html(post_id):
    data = get_post_page_html(post_id)
    post_html = BeautifulSoup(data, 'html.parser')
    video_element = post_html.find("meta", {"property": "og:video"})
    if not video_element:
        return None
    return format_page_json(post_html, post_id)


def get_video_json_from_graphql(post_id):
    data = get_post_graphql_data(post_id)
    media_data = data.get("data", {}).get("xdt_shortcode_media")
    if not media_data:
        return None
    if not media_data.get("is_video"):
        raise HTTPError("This post is not a video", 400)
    return format_graphql_json(media_data, post_id)


def get_video_info(post_id: str) -> Dict[str, Any]:
    try:
        video_info = get_video_json_from_html(post_id)
        if video_info:
            return video_info
    except Exception:
        pass

    try:
        video_info = get_video_json_from_graphql(post_id)
        if video_info:
            return video_info
    except Exception:
        pass

    raise ValueError("Video link for this post is not public or accessible.")


def get_post_page_html(post_id):
    url = f"https://www.instagram.com/p/{post_id}/"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.5",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "upgrade-insecure-requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    }
    response = requests.get(url, headers=headers)
    if not response.ok:
        raise ValueError(f"Failed to fetch Instagram page: {response.status_code}")
    return response.text


def get_post_graphql_data(post_id):
    encoded_data = encode_graphql_request_data(post_id)
    url = "https://www.instagram.com/api/graphql"
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-FB-Friendly-Name": "PolarisPostActionLoadPostQueryQuery",
        "X-CSRFToken": "RVDUooU5MYsBbS1CNN3CzVAuEP8oHB52",
        "X-IG-App-ID": "1217981644879628",
        "X-FB-LSD": "AVqbxe3J_YA",
        "X-ASBD-ID": "129477",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36",
    }
    response = requests.post(url, data=encoded_data, headers=headers)
    if not response.ok:
        raise ValueError(f"GraphQL request failed: {response.status_code}")
    return response.json()