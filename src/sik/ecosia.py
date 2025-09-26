import asyncio
from urllib.parse import quote_plus
from typing import List, Optional

import curl_cffi.requests as requests
from selectolax.parser import HTMLParser

from .common import SearchResult, logger


async def fetch_page(session: requests.AsyncSession, url: str) -> str:
    resp = await session.get(url, impersonate="firefox135")
    return resp.text


def parse_results(html_text: str) -> List[SearchResult]:
    tree = HTMLParser(html_text)
    serp: List[SearchResult] = []

    for node in tree.css('[data-test-id="mainline-result-web"]'):
        link_node = node.css_first('[data-test-id="result-link"]')
        title_node = node.css_first('[data-test-id="result-title"]')
        snippet_node = node.css_first('[data-test-id="web-result-description"]')

        link: Optional[str] = link_node.attrs.get("href") if link_node else None
        title: Optional[str] = title_node.text(strip=True) if title_node else None
        snippet: Optional[str] = snippet_node.text(strip=True) if snippet_node else None

        if link and title:
            assert isinstance(link, str) and isinstance(title, str)
            serp.append({
                "link": link,
                "title": title,
                "snippet": snippet
            })

    return serp


async def search_ecosia(query: str, pages: int = 1) -> List[SearchResult]:
    query = quote_plus(query)
    urls = [f"https://www.ecosia.org/search?method=index&q={query}"]
    if pages > 1:
        urls += [f"https://www.ecosia.org/search?method=index&q={query}&p={i}" for i in range(1, pages)]

    logger.info(f"Ecosia: fetching {pages} page(s) for query='{query}'")

    async with requests.AsyncSession() as session:
        html_texts = await asyncio.gather(*(fetch_page(session, url) for url in urls))

    all_results: List[SearchResult] = []
    for idx, html in enumerate(html_texts, start=1):
        logger.info(f"Ecosia: parsing page {idx}/{len(html_texts)}")
        all_results.extend(parse_results(html))

    logger.info(f"Ecosia: total results={len(all_results)}")
    return all_results
