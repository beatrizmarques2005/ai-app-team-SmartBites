import json
from langfuse import observe

class IngredientService:
    """Check inventory and suggest AI-based replacements."""

    def __init__(self, inventory, ai_service):
        self.inventory = inventory
        self.ai = ai_service

    @observe()
    def check_missing(self, recipe):
        missing = []
        inv = [i.lower() for i in self.inventory.get_ingredients_for_recipe()]

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
