import curl_cffi.requests as requests
from urllib.parse import quote_plus
from selectolax.parser import HTMLParser
import asyncio

# TODO
# ADD PROXY
# Works for now.

async def fetch_page(session, url):
    resp = await session.get(url, impersonate="firefox135")
    return resp.text

async def search_ecosia(query: str, pages: int = 0):
    query = quote_plus(query)
    urls = [f"https://www.ecosia.org/search?method=index&q={query}"]
    if pages > 1:
        urls += [f"https://www.ecosia.org/search?method=index&q={query}&p={i}" for i in range(1, pages)]

    
    async with requests.AsyncSession() as session:
        html_texts = await asyncio.gather(*(fetch_page(session, url) for url in urls))
    
    serp = []
    for html_text in html_texts:
        tree = HTMLParser(html_text)
        for node in tree.css('[data-test-id="mainline-result-web"]'):
            link_node = node.css_first('[data-test-id="result-link"]')
            title_node = node.css_first('[data-test-id="result-title"]')
            snippet_node = node.css_first('[data-test-id="web-result-description"]')
            
            serp.append({
                "link": link_node.attributes.get("href") if link_node else None,
                "title": title_node.text(strip=True) if title_node else None,
                "snippet": snippet_node.text(strip=True) if snippet_node else None
            })
    return serp