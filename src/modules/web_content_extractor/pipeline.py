from typing import Dict, Any, List
from fastapi import WebSocket
from src.modules.web_content_extractor.queryOptimizer import optimize_query
from src.modules.web_content_extractor.relevant_content_extractor import relevant_content_extractor
from src.modules.web_content_extractor.search import get_search_results

async def pipeline(query: str , websocket: WebSocket = None) -> Dict[str, Any]:
    if not query or not isinstance(query, str):
        return {"summary": [], "sources": [], "error": "Invalid query"}
    
    optimized_query = optimize_query(query)
    urls = get_search_results(optimized_query)
    
    if not urls:
        return {"summary": [], "sources": [], "error": "No search results found"}
    results = await relevant_content_extractor(urls, query,websocket=websocket)

    return {"sources": urls , "results": results}

