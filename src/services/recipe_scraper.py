import os
import re
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langfuse import observe


class RecipeScraper:
    """Unified recipe crawler + scraper."""

    def __init__(self, ai_service):
        self.ai = ai_service
        # Prefer RECIPES_SOURCES (new name), then RECIPES_SOURCE, then RECIPE_SOURCES
        sources_env = os.getenv("RECIPES_SOURCES") or os.getenv("RECIPES_SOURCE") or os.getenv("RECIPE_SOURCES")

        # If not present in the process environment, try to read the project's .env file
        # to support array-style entries like RECIPES_SOURCES=( ... ) that some dotenv
        # loaders don't parse into os.environ.
        if not sources_env:
            try:
                from pathlib import Path
                repo_root = Path(__file__).resolve().parents[2]
                env_path = repo_root / '.env'
                if env_path.exists():
                    text = env_path.read_text(encoding='utf-8')
                    # Try to find a RECIPES_SOURCES=... line or a RECIPES_SOURCES(...) block
                    m = re.search(r'RECIPES_SOURCES\s*=\s*\(([^)]*)\)', text, re.IGNORECASE | re.DOTALL)
                    if m:
                        sources_env = m.group(1)
                    else:
                        m2 = re.search(r'RECIPES_SOURCES\s*=\s*(.+)', text)
                        if m2:
                            sources_env = m2.group(1)
            except Exception:
                sources_env = None

        if sources_env:
            # Extract URLs from a variety of possible formats (comma-separated, newline-separated,
            # quoted, or a bash-style array). Use a regex to robustly find https? URLs.
            found = re.findall(r"https?://[^\s\",)']+", sources_env)
            self.default_sources = found
        else:
            self.default_sources = []

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
        """Collect recipe links from the provided sources (or env RECIPES_SOURCE / RECIPE_SOURCES)."""
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
