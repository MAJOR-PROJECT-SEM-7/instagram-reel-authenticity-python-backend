import httpx
from bs4 import BeautifulSoup

def clean_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    return ' '.join(soup.stripped_strings)

def scrape_all_urls(urls):
    data = []
    for url in urls:
        try:
            resp = httpx.get(url, timeout=10)
            text = clean_text(resp.text)
            data.append({"url": url, "text": text})
        except:
            continue
    return data
