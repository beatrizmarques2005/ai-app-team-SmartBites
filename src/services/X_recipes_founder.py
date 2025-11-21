# no idea yet
import logging
import os
import requests
from bs4 import BeautifulSoup
from services.ai_service import AIService

logger = logging.getLogger(__name__)

class RecipeService:
    def __init__(self):
        self.ai = AIService()
        # load from env automatically
        self.recipe_urls = os.getenv("RECIPES_URLS", "").strip("()").split()

    def fetch_page(self, url):
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            logger.exception("Could not fetch %s: %s", url, e)
            return None

    def search_recipes(self, query: str) -> list:
        """
        Searches all recipe sites for recipes matching a user query.
        """
        results = []

        for url in self.recipe_urls:
            logger.debug("Searching in %s", url)
            html = self.fetch_page(url)

            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(" ", strip=True)

            if query.lower() in text.lower():
                logger.debug("Found potential match at %s — extracting with AI", url)
                recipe = self.ai.extract_recipe_from_html(html)
                results.append(recipe)

        return results
