
from langfuse import observe

class IngredientService:
    def __init__(self):
        # TODO: Initialize DB connection
        pass
        # self.client = MongoClient("mongodb://localhost:27017")
        # self.db = self.client["kitchen"]
        # self.collection = self.db["ingredients"]

    @observe()
    def check_ingredients(self, recipe_ingredients: list):
        missing = []
        available = []

        for ing in recipe_ingredients:
            name = ing.split()[1] if " " in ing else ing

            match = self.collection.find_one({"name": {"$regex": name, "$options": "i"}})

            if match:
                available.append({"ingredient": ing, "status": "ok"})
            else:
                missing.append(name)

        return available, missing

    @observe()
    def suggest_replacement(self, ingredient: str):
        """
        AI or rule-based replacement suggestions.
        This version is simple; you can plug in AI later.
        """
        # TODO: Integrate AI model for better suggestions

        replacements = {
            "tomato": ["tinned tomatoes", "passata", "tomato sauce"],
            "milk": ["soy milk", "oat milk", "cream"],
        }

        return replacements.get(ingredient.lower(), [])
