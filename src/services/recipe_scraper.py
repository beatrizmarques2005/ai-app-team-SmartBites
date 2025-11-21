import requests
from langfuse import observe

class RecipeScraper:
    def __init__(self, ai_service):
        self.ai = ai_service

    @observe()
    def scrape(self, url: str):
        try:
            html = requests.get(url, timeout=6).text
        except:
            return None

        recipe = self.ai.extract_recipe(html)
        return recipe
