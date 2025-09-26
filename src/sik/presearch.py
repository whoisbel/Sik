import asyncio
import random
from urllib.parse import quote_plus
from typing import List, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from selectolax.parser import HTMLParser

from .common import SearchResult, logger


async def fetch_page(context, url: str) -> str:
    page = await context.new_page()
    await asyncio.sleep(random.uniform(1, 3))
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_selector("a.text-base", timeout=20000)
    except PlaywrightTimeoutError:
        logger.warning(f"Presearch: timeout while loading {url}, returning partial content...")
    html = await page.content()
    await page.close()
    return html


def parse_results(html_text: str) -> List[SearchResult]:
    tree = HTMLParser(html_text)
    serp: List[SearchResult] = []

    for block in tree.css("div.relative.p-4"):
        link_node = block.css_first("a.flex.items-center")
        title_node = block.css_first("a.text-base span")
        snippet_node = block.css_first("div.mt-1.text-gray-800")

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


async def search_presearch(query: str, pages: int = 1) -> List[SearchResult]:
    query = quote_plus(query)
    all_results: List[SearchResult] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        for page_num in range(1, pages + 1):
            url = f"https://presearch.com/search?q={query}&page={page_num}"
            logger.info(f"Presearch: fetching page {page_num}/{pages}")
            html = await fetch_page(context, url)
            all_results.extend(parse_results(html))
            await asyncio.sleep(random.uniform(1, 3))
        await browser.close()

    logger.info(f"Presearch: total results={len(all_results)}")
    return all_results
