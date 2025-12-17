import json
from typing import Optional
from langfuse import observe

class IngredientService:
    """Check inventory and suggest AI-based replacements."""

    def __init__(self, inventory, ai_service):
        self.inventory = inventory
        self.ai = ai_service

    @observe()
    def check_missing(self, recipe, user_id: Optional[str] = None):
        missing = []
        # Support inventory implementations that accept an optional user_id
        try:
            inv_list = self.inventory.get_ingredients_for_recipe()
        except TypeError:
            try:
                inv_list = self.inventory.get_ingredients_for_recipe(user_id) if user_id else self.inventory.get_ingredients_for_recipe()
            except Exception:
                inv_list = []

        inv = [i.lower() for i in (inv_list or [])]

        for ingredient in recipe.get("ingredients", []):
            name = ingredient.lower()
            if not any(item in name for item in inv):
                missing.append(ingredient)

        return missing

    @observe()
    def suggest_replacement(self, ingredient: str, context=None):
        question = f"Suggest 3 suitable replacements for '{ingredient}'"
        if context:
            question += f" in the context of {context}"

        ai_response = self.ai.ask_recipe_question(
            recipe={"ingredients": [ingredient]},
            question=question
        )

        try:
            replacements = json.loads(ai_response)
            if isinstance(replacements, list):
                return replacements
        except:
            pass

        # fallback: split text by commas
        return [r.strip() for r in ai_response.split(",") if r.strip()]
