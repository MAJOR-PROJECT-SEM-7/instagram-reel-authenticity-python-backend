from typing import Dict, Any, List
from src.websearchengine.search import get_search_results
from src.websearchengine.scraper import scrape_all_urls
from src.websearchengine.embedder import embed_and_search
from src.websearchengine.summarizer import summarize_data
from src.websearchengine.queryOptimizer import optimize_query
from fastapi import WebSocket

async def pipeline(query: str , websocket: WebSocket = None) -> Dict[str, Any]:
    if not query or not isinstance(query, str):
        return {"summary": [], "sources": [], "error": "Invalid query"}
    
    optimized_query = optimize_query(query)
    urls = get_search_results(optimized_query)
    # print(urls)
    
    if not urls:
        return {"summary": [], "sources": [], "error": "No search results found"}
    
    raw_data = await scrape_all_urls(urls , websocket)
    # print(raw_data)
    
    if not raw_data:
        return {"summary": [], "sources": urls, "error": "Failed to scrape content"}
    
    results = embed_and_search(raw_data, query)
    # print(results)
    summary = summarize_data(results, query)
    # print(summary)
    return {"summary": summary, "sources": urls , "score": results}
    # return {"summary": summary, "sources": urls}
