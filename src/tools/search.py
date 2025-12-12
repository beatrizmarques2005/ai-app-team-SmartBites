import requests
from bs4 import BeautifulSoup
import google.genai as genai
from google.genai import types
import os

class Search:
    """
    Wrapper tool enabling Gemini to use Google Search and URL Context.
    Also returns the actual recipe URL if available.
    """

    def __init__(self):
        self.client = genai.Client()
        self.model = os.getenv("MODEL")

    def find_recipe_url(self, recipe_name: str, site: str = "pingodoce.pt") -> str:
        """Return first URL from the allowed site matching the recipe name."""
        query = f"{recipe_name} site:{site}"
        headers = {"User-Agent": "Gemini-Agent/1.0"}
        search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"

        try:
            r = requests.get(search_url, headers=headers, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.find_all("a"):
                href = a.get("href", "")
                if href.startswith("/url?q="):
                    url = href.split("/url?q=")[1].split("&")[0]
                    if site in url:
                        return url
        except Exception as e:
            return f"Error fetching search results: {e}"

        return ""  # No URL found

    def run(self, recipe_name: str = None, query: str = None, urls: list[str] = None):
        """
        Returns:
            - recipe_url: direct link to the recipe
            - search_results: optional search content
            - url_context: fetched text content from provided URLs
        """
        result = {"recipe_url": None, "search_results": None, "url_context": None}

        # 1. Find the direct recipe URL
        if recipe_name:
            result["recipe_url"] = self.find_recipe_url(recipe_name)

        # 2. Optional Google search
        if query:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"Search the web for: {query}",
                config=types.GenerateContentConfig(tools=[{"google_search": {}}]),
            )
            result["search_results"] = getattr(response, "text", "")

        # 3. Optional URL content fetch
        if urls:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"Fetch and summarize the following URLs:\n{urls}",
                config=types.GenerateContentConfig(tools=[{"url_context": {}}]),
            )
            result["url_context"] = getattr(response, "text", "")

        return result
