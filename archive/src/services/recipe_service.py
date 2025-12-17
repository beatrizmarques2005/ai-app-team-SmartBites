"""RecipeService - search, generate and fetch recipes.

This service wraps existing recipe generator/crawling logic and provides
methods recommended in NOTES.md.
"""
from typing import List, Dict, Any, Optional
from .ai_service import AIService
from ..db.supabase_adapter import SupabaseAdapter


class RecipeService:
    def __init__(self, api_key: Optional[str] = None, adapter: Optional[SupabaseAdapter] = None):
        self.ai_gen = AIService(api_key=api_key or '')
        self.adapter = adapter or SupabaseAdapter()

    def search_by_ingredients(self, ingredients: List[str], strict: bool = True) -> List[Dict[str, Any]]:
        # Prefer X_meal_planner if available, otherwise fallback to recipe_generator search
        try:
            from ..tools.meal_planner import match_ingredients_to_recipes
            matched = match_ingredients_to_recipes(ingredients)
        except Exception:
            # fallback: simple match using ai_gen or empty
            matched = []

        if strict:
            return [r for r in matched if not r.get('missing_ingredients')]
        return matched

    def get_saved_recipes(self, user_id: str) -> List[Dict[str, Any]]:
        if not getattr(self.adapter, '_has_table', False):
            return []
        resp = self.adapter.client.table('recipes').select('*').eq('user_id', user_id).execute()
        return getattr(resp, 'data', []) or []

    def generate_from_pantry(self, inventory_manager, servings: int = 1, dietary: Optional[str] = None) -> Dict[str, Any]:
        # inventory_manager should implement get_ingredients_for_recipe()
        return self.ai_gen.generate_recipe(inventory_manager, servings=servings, dietary=dietary)
