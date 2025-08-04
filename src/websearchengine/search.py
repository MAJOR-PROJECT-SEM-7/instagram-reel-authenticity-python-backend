from duckduckgo_search import DDGS

def get_search_results(query, max_results=10):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    return [r['href'] for r in results]
