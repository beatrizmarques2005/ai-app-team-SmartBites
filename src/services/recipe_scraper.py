import os
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langfuse import observe


class RecipeScraper:
    """Unified recipe crawler + scraper.

    Methods:
    - fetch_html(url)
    - collect_links(sources)
    - scrape(url)
    - search_recipes(query, sources=None)
    """

    def __init__(self, ai_service):
        self.ai = ai_service
        self.default_sources = os.getenv("RECIPE_SOURCES", "").split(",") if os.getenv("RECIPE_SOURCES") else []

    @observe()
    def fetch_html(self, url: str) -> Optional[str]:
        try:
            r = requests.get(url, timeout=8)
            r.raise_for_status()
            return r.text
        except Exception:
            return None

    @observe()
    def collect_links(self, sources: Optional[List[str]] = None) -> List[str]:
        """Collect recipe links from the provided sources (or env RECIPE_SOURCES)."""
        srcs = sources or self.default_sources
        links: List[str] = []
        for base in srcs:
            html = self.fetch_html(base)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(k in href.lower() for k in ["receita", "receitas", "recipe"]):
                    if href.startswith("http"):
                        links.append(href)
                    else:
                        links.append(base.rstrip("/") + "/" + href.lstrip("/"))
        return list(set(links))

    @observe()
    def scrape(self, url: str) -> Optional[dict]:
        """Fetch and extract a recipe from a URL using the AI service."""
        html = self.fetch_html(url)
        if not html:
            return None
        return self.ai.extract_recipe(html)

    @observe()
    def search_recipes(self, query: str, sources: Optional[List[str]] = None, max_results: int = 20) -> List[dict]:
        """Search recipe sites for pages matching `query` and extract recipes."""
        results: List[dict] = []
        links = self.collect_links(sources)
        for url in links[:max_results]:
            html = self.fetch_html(url)
            if not html:
                continue
            if query.lower() in html.lower():
                recipe = self.ai.extract_recipe(html)
                if recipe:
                    results.append({"url": url, **recipe})
        return results
