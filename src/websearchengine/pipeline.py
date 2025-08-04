from src.websearchengine.search import get_search_results
from src.websearchengine.scraper import scrape_all_urls
from src.websearchengine.embedder import embed_and_search
# from src.websearchengine.summarizer import summarize_data

def pipeline(query: str):
    urls = get_search_results(query)
    raw_data = scrape_all_urls(urls)
    results = embed_and_search(raw_data, query)
    # summary = summarize_data(results, query)
    return {"summary": results, "sources": urls}
    # return {"summary": summary, "sources": urls}
