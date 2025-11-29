"""RecipeService - search, generate and fetch recipes.

This service wraps existing recipe generator/crawling logic and provides
methods recommended in NOTES.md.
"""
from typing import List, Dict, Any, Optional
from ..services.recipe_generator import RecipeGeneratorAI
from ..services.X_meal_planner import match_ingredients_to_recipes, _get_recipe_db
from ..db.supabase_adapter import SupabaseAdapter


class RecipeService:
    def __init__(self, api_key: Optional[str] = None):
        self.ai_gen = RecipeGeneratorAI(api_key or '')
        self.adapter = SupabaseAdapter()

    def search_by_ingredients(self, ingredients: List[str], strict: bool = True) -> List[Dict[str, Any]]:
        # Use X_meal_planner matching for quick local search
        matched = match_ingredients_to_recipes(ingredients)
        if strict:
            return [r for r in matched if not r.get('missing_ingredients')]
        return matched

    def get_saved_recipes(self, user_id: str) -> List[Dict[str, Any]]:
        resp = self.adapter.client.table('recipes').select('*').eq('user_id', user_id).execute()
        return getattr(resp, 'data', []) or []

    def generate_from_pantry(self, inventory_manager, servings: int = 1, dietary: Optional[str] = None) -> Dict[str, Any]:
        # inventory_manager should implement get_ingredients_for_recipe()
        return self.ai_gen.generate_recipe(inventory_manager, servings=servings, dietary=dietary)
