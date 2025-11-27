import aiohttp
import asyncio
from bs4 import BeautifulSoup
from langfuse import observe

class RecipeCrawler:
    """Collect recipe links from multiple supermarket websites."""

    def __init__(self, sources: list[str]):
        self.sources = sources

    async def fetch_html(self, session, url):
        try:
            async with session.get(url, timeout=10) as resp:
                return await resp.text()
        except:
            return None

    @observe()
    async def collect_links(self) -> list[str]:
        links = []

        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_html(session, url) for url in self.sources]
            htmls = await asyncio.gather(*tasks)

            for base, html in zip(self.sources, htmls):
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
