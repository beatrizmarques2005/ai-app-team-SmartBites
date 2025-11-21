
import requests
from bs4 import BeautifulSoup
from langfuse import observe

class RecipeCrawler:
    def __init__(self, base_url: str):
        self.base_url = base_url

    @observe()
    def get_all_recipe_links(self) -> list:
        """Returns a list of full recipe URLs found on the recipe page."""

        try:
            html = requests.get(self.base_url, timeout=5).text
        except Exception as e:
            print(f"Cannot fetch {self.base_url}: {e}")
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Many supermarket sites use links like <a href="/receitas/...">
        links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "receita" in href or "recipes" in href or "receitas" in href:
                # Normalize link
                if href.startswith("http"):
                    links.append(href)
                else:
                    links.append(self.base_url.rstrip("/") + "/" + href.lstrip("/"))

        return list(set(links))
