import logging
from typing import Optional, TypedDict


class SearchResult(TypedDict):
    link: str
    title: str
    snippet: Optional[str]


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("search")
