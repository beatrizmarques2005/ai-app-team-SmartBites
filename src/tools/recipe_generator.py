import openai
import json 
from inventory import InventoryTool

class RecipeGeneratorAI:
    def __init__(self, api_key: str):
        openai.api_key = api_key
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
        