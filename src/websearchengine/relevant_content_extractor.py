import httpx
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
import asyncio
import json
from fastapi import WebSocket

model = SentenceTransformer('all-MiniLM-L6-v2')

def clean_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    return ' '.join(soup.stripped_strings)

async def fetch_url(client, url,websocket:WebSocket=None):
    """Fetch a single URL asynchronously and return cleaned text."""
    try:
        if websocket:
            await websocket.send_text(json.dumps({"step": "processing", "message": f"Reading: {url}"}))
        resp = await client.get(url, timeout=10)
        text = clean_text(resp.text)
        return {"url": url, "text": text}
    except Exception:
        return None

async def relevant_content_extractor(urls, query, top_k=5,websocket:WebSocket=None):
    """Scrapes URLs concurrently, embeds, and returns relevant content with similarity scores."""
    # 1. Scrape pages concurrently
    async with httpx.AsyncClient() as client:
        tasks = [fetch_url(client, url,websocket=websocket) for url in urls]
        docs = await asyncio.gather(*tasks)

    # Filter out failed fetches
    docs = [doc for doc in docs if doc]

    if not docs:
        return []

    # 2. Prepare embeddings
    doc_texts = [doc['text'][:1000] for doc in docs]  
    embeddings = model.encode(doc_texts, batch_size=8, show_progress_bar=False)

    # 3. Fit Nearest Neighbors
    nn_model = NearestNeighbors(
        n_neighbors=min(top_k, len(doc_texts)), 
        metric='cosine'
    )
    nn_model.fit(embeddings)

    # 4. Query embedding
    q_embed = model.encode([query])
    distances, indices = nn_model.kneighbors(q_embed)

    # 5. Collect results with scores
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if 0 <= idx < len(doc_texts):
            similarity = float(1 - dist) 
            results.append({
                "url": docs[idx]['url'],
                "snippet": doc_texts[idx],
                "score": round(similarity, 4)
            })

    return results
