
import requests
from services.ai_service import AIService
from langfuse import observe

class RecipeScraper:
    def __init__(self):
        self.ai = AIService()

    @observe()
    def scrape_recipe(self, url: str) -> dict:
        """Fetch recipe page and extract structured recipe JSON."""
        try:
            html = requests.get(url, timeout=6).text
        except:
            print(f"⚠️ Cannot fetch recipe page: {url}")
            return None

        try:
            recipe = self.ai.extract_recipe_from_html(html)
            return recipe
        except Exception as e:
            print(f"⚠️ AI extraction failed for {url}: {e}")
            return None

