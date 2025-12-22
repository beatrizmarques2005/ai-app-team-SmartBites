"""
Recipe Writer Module
--------------------

Handles inserting recipes into the database after user approval, ensuring no duplicates based on recipe name, meal type, and meal date.

"""

from datetime import datetime
from typing import List
from langfuse import observe

from src.authentication import AuthService
from src.db.client import supabase

class RecipeWriter:
    """Insert recipes into the DB after explicit user approval, including meal_type and meal_date."""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if not self.user_id:
            raise ValueError("User must be authenticated.")

    @observe()
    def recipe_exists(self, recipe_name: str, meal_type: str, date: datetime) -> bool:
        """
        Checks if a recipe exists in the database for a specific user, meal type, and date.

        Args:
            recipe_name (str): The name of the recipe to check.
            meal_type (str): The type of meal (e.g., breakfast, lunch, dinner).
            date (datetime): The date associated with the meal.

        Returns:
            bool: True if the recipe exists for the given user, meal type, and date; otherwise, False.
        """
        res = (
            supabase.table("recipes")
            .select("id")
            .eq("user_id", self.user_id)
            .eq("recipe_name", recipe_name)
            .eq("meal_type", meal_type)
            .eq("meal_date", date)
            .execute()
        )
        return bool(res.data)

    @observe()
    def add_recipes(self, recipes: List[dict], user_approval: bool = False) -> List[dict]:
        """
        Adds a list of recipes to the database after user approval.
        Parameters:
        ----------
        recipes : List[dict]
            A list of dictionaries where each dictionary contains the details of a recipe, including:
            - recipe_name (str): The name of the recipe.
            - ingredients (list): A list of ingredients required for the recipe.
            - instructions (str): The cooking instructions for the recipe.
            - source_url (str, optional): A URL linking to the recipe source.
            - link (str, optional): An alternative link to the recipe.
            - recipe_date (str, optional): The date the recipe was created or modified.
            - meal_type (str or list, optional): The type of meal (e.g., "breakfast", "lunch", "dinner").
            - meal_date (str, optional): The date the meal is intended to be served.
        user_approval : bool, optional
            A flag indicating whether the user has approved the addition of recipes. Default is False.
        Returns:
        -------
        List[dict]
            A list of dictionaries representing the recipes that were successfully inserted into the database,
            each including the recipe ID assigned by the database.
        """
        if not user_approval:
            print("Recipes not inserted: awaiting user approval.")
            return []

        inserted = []
        skipped = []

        for r in recipes:
            recipe_name = r.get("recipe_name")
            ingredients = r.get("ingredients")
            instructions = r.get("instructions")
            link = r.get("source_url") or r.get("link")
            recipe_date = r.get("recipe_date") or datetime.utcnow().isoformat()
            meal_type = r.get("meal_type")  # e.g., "breakfast", "lunch", "dinner"
            meal_date = r.get("meal_date") or datetime.utcnow().date().isoformat()

            if self.recipe_exists(recipe_name, meal_type, meal_date):
                skipped.append(recipe_name)
                continue

            if isinstance(meal_type, list):
                meal_type = meal_type[0] if meal_type else None

            record = {
                "recipe_name": recipe_name,
                "ingredients": ingredients.lower() if isinstance(ingredients, str) else ingredients,
                "instructions": instructions,
                "recipe_date": recipe_date,
                "link": link,
                "meal_type": meal_type.lower() if meal_type else None,
                "meal_date": meal_date,
                "user_id": self.user_id,
            }

            try:
                insert_res = supabase.table("recipes") \
                    .insert(record, returning="representation") \
                    .execute()
                
            except Exception as e:
                print(f"Error inserting recipe '{recipe_name}': {e}")
                continue

            if insert_res.data and len(insert_res.data) > 0:
                record["id"] = insert_res.data[0]["id"]
                inserted.append(record)
                print(f"Stored recipe: {recipe_name} for {meal_type} on {meal_date} (ID: {record['id']})")
            else:
                print(f"Recipe '{recipe_name}' inserted but ID not returned.")

        if skipped:
            print("Skipped (already saved): " + ", ".join(skipped))

        return inserted


