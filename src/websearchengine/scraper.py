import httpx
from bs4 import BeautifulSoup
from fastapi import WebSocket
import json

def clean_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    return ' '.join(soup.stripped_strings)

async def scrape_all_urls(urls, websocket: WebSocket = None):
    data = []
    for url in urls:
        if websocket:
            await websocket.send_text(json.dumps({"step": "processing", "message": f"Reading {url}"}))
        try:
            resp = httpx.get(url, timeout=10)
            text = clean_text(resp.text)
            data.append({"url": url, "text": text})
        except:
            continue
    return data
