# no idea yet
import os
import requests
from bs4 import BeautifulSoup
from services.ai_service import AIService

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
        except Exception as e:
            print(f"⚠️ Could not fetch {url}: {e}")
            return None

    def search_recipes(self, query: str) -> list:
        """
        Searches all recipe sites for recipes matching a user query.
        """
        results = []

        for url in self.recipe_urls:
            print(f"🔍 Searching in {url}...")
            html = self.fetch_page(url)

            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(" ", strip=True)

            if query.lower() in text.lower():
                print("  -> Found potential match! Extracting with AI...")
                recipe = self.ai.extract_recipe_from_html(html)
                results.append(recipe)

        return results
