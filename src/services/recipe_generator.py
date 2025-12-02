"""Shim for recipe generation.

This file provides a lightweight `RecipeGeneratorAI` class so the package
imports cleanly even when the full AI stack or external SDKs are not
available. When an `AIService` instance exists it will delegate to it;
otherwise it returns a simple placeholder response.
"""
from typing import Any, Dict

try:
    from .ai_service import AIService
    _HAS_AI = True
except Exception:
    AIService = None
    _HAS_AI = False


class RecipeGeneratorAI:
    def __init__(self, ai_service: AIService = None):
        # prefer injected service; fall back to constructing one if available
        self.ai = ai_service or (AIService() if _HAS_AI else None)

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate a recipe from a prompt.

        If a proper AIService is available we delegate; otherwise return a
        deterministic placeholder suitable for demos and tests.
        """
        if self.ai and hasattr(self.ai, "generate_recipe"):
            return self.ai.generate_recipe(prompt, **kwargs)

        # Minimal deterministic fallback used in demo mode or tests that don't
        # call external APIs.
        return {
            "title": "Sample Recipe",
            "prompt": prompt,
            "ingredients": [
                {"name": "1 cup flour", "quantity": 1, "unit": "cup"},
                {"name": "1 egg", "quantity": 1, "unit": "unit"},
            ],
            "instructions": "Mix ingredients and cook until done.",
        }


__all__ = ["RecipeGeneratorAI"]
import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langfuse import observe
import openai
from .pantry_service import PantryService

logger = logging.getLogger(__name__)

# RecipeCrawler → crawling only
# RecipeScraper → AI parsing only
# IngredientService → DB + ingredient checking
# AIService → generic AI functions
# RecipeGeneratorAI → orchestrates everything

load_dotenv()


class RecipeGeneratorAI:
    """Compatibility shim that delegates to `AIService`.

    The legacy `RecipeGeneratorAI` implementation used OpenAI directly. The
    functionality has been moved to `AIService`. This shim preserves the
    previous public interface while delegating to the consolidated AIService.
    """

    def __init__(self, api_key: str):
        # AIService will read API key from env or accept it; instantiate accordingly
        from .ai_service import AIService

        # prefer passing api_key through AIService constructor when supported
        try:
            self.ai = AIService(api_key=api_key)
        except Exception:
            self.ai = AIService()

    @observe()
    def generate_recipe(self, inventory_manager, servings=1, dietary=None):
        return self.ai.generate_recipe(inventory_manager, servings=servings, dietary=dietary)

    @observe()
    def get_recipe_links(self):
        return self.ai.get_recipe_links()

    @observe()
    def extract_recipe_from_html(self, html: str):
        return self.ai.extract_recipe_from_html(html)

    @observe()
    def get_supermarket_recipes(self, max_recipes=5):
        return self.ai.get_supermarket_recipes(max_recipes=max_recipes)

    @observe()
    def check_ingredients(self, recipe, inventory_manager: PantryService):
        return self.ai.check_ingredients(recipe, inventory_manager)

    @observe()
    def get_possible_recipes(self, inventory_manager: PantryService):
        return self.ai.get_possible_recipes(inventory_manager)

        