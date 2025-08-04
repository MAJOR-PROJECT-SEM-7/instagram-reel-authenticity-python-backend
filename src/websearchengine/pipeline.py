from src.websearchengine.search import get_search_results
from src.websearchengine.scraper import scrape_all_urls
from src.websearchengine.embedder import embed_and_search
from src.websearchengine.summarizer import summarize_data

def pipeline(query: str):
    if not query or not isinstance(query, str):
        return {"summary": [], "sources": [], "error": "Invalid query"}
    
    urls = get_search_results(query)
    print(urls)
    
    if not urls:
        return {"summary": [], "sources": [], "error": "No search results found"}
    
    raw_data = scrape_all_urls(urls)
    print(raw_data)
    
    if not raw_data:
        return {"summary": [], "sources": urls, "error": "Failed to scrape content"}
    
    results = embed_and_search(raw_data, query)
    print(results)
    summary = summarize_data(results, query)
    print(summary)
    return {"summary": summary, "sources": urls}
    # return {"summary": summary, "sources": urls}
