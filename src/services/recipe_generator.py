import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langfuse import observe
import openai
from src.tools.inventory import InventoryTool

logger = logging.getLogger(__name__)

# RecipeCrawler → crawling only
# RecipeScraper → AI parsing only
# IngredientService → DB + ingredient checking
# AIService → generic AI functions
# RecipeGeneratorAI → orchestrates everything

load_dotenv()

class RecipeGeneratorAI:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.recipe_sources = os.getenv("RECIPE_SOURCES", "").split(",")

    @observe()
    def generate_recipe(self, inventory_manager: InventoryTool, servings=1, dietary=None):

        ingredients = inventory_manager.get_ingredients_for_recipe()

        if not ingredients:
            return "No available ingredients to elaborate a recipe."
             
        prompt = (
            f"Create a detailed recipe using these ingredients: {', '.join(ingredients)}"
            f"Prioritize ingredients that are close to their expiration date."
            f"Adjust quantities for {servings} serving(s)."
        )

        if dietary:
            prompt += f"Make it suitable and safe for a {dietary} diet."

        prompt += "Return the recipe as JSON with title, servings, ingredients with quantities, and steps as keys."
        response = openai.ChatCompletion.create(
            model = "2.5-flashlight",
            messages=[{"role": "user", "content": prompt}],
            temperature = 0.7
        )

        text_response = response.choices[0].message.content.strip()
        try:
            recipe = json.loads(text_response)
        except json.JSONDecodeError:
            return "Error: Unable to parse recipe response."
        return recipe
    
    @observe()
    def get_recipe_links(self):
        urls = []
        for site in self.recipe_sources:
            try:
                html = requests.get(site, timeout=5).text
            except requests.RequestException as e:
                logger.debug("Failed to fetch %s: %s", site, e)
                continue
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "receita" in href or "receitas" in href or "recipe" in href:
                    if href.startswith("http"):
                        urls.append(href)
                    else:
                        # Normalize
                        base = site.rstrip("/")
                        urls.append(base + "/" + href.lstrip("/"))
        return list(set(urls))

    @observe()   
    def extract_recipe_from_html(self, html: str):
        prompt = f"""
        Extract a recipe from the following HTML.
        Return ONLY valid JSON.
        JSON fields:
        - title (string)
        - ingredients (list of strings)
        - instructions (list of steps)
        - estimated_time (int, minutes)
        HTML:
        {html}
        """
        response = openai.ChatCompletion.create(
            model="2.5-flashlight",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        text = response.choices[0].message.content.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.exception("Failed to parse extracted recipe JSON: %s", e)
            return None

    @observe()
    def get_supermarket_recipes(self, max_recipes=5):
        recipe_links = self.get_recipe_links()
        collected = []

        for link in recipe_links[:max_recipes]:
            try:
                html = requests.get(link, timeout=5).text
                recipe = self.extract_recipe_from_html(html)
                if recipe:
                    collected.append({ "url": link, **recipe })
            except requests.RequestException as e:
                logger.debug("Failed to fetch recipe link %s: %s", link, e)
                continue
        
        return collected

    @observe()
    def check_ingredients(self, recipe, inventory_manager: InventoryTool):
        available = inventory_manager.get_ingredients_for_recipe()
        missing = []

        for item in recipe["ingredients"]:
            base = item.lower()
            found = False

            for inv in available:
                if inv.lower() in base:
                    found = True
                    break
            if not found:
                missing.append(item)

        return missing

    @observe()
    def get_possible_recipes(self, inventory_manager: InventoryTool):
        supermarket_recipes = self.get_supermarket_recipes(max_recipes=10)
        possible = []

        for recipe in supermarket_recipes:
            missing = self.check_ingredients(recipe, inventory_manager)

            if len(missing) == 0:
                possible.append(recipe)
            else:
                recipe["missing_ingredients"] = missing

        return possible

        