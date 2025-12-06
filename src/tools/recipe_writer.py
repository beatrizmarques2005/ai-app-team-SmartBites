from datetime import datetime
from typing import List
from langfuse import observe
from src.services.auth_service import AuthService
from src.db.client import supabase

class RecipeWriter:
    """Insert recipes into the DB after explicit user approval, including meal_type and meal_date."""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if not self.user_id:
            raise ValueError("User must be authenticated.")

    # ---------------- Duplicate Check ----------------
    def recipe_exists(self, recipe_name: str) -> bool:
        res = (
            supabase.table("recipes")
            .select("id")
            .eq("user_id", self.user_id)
            .eq("recipe_name", recipe_name)
            .execute()
        )
        return bool(res.data)

    # ---------------- Insert Recipes ----------------
    @observe()
    def add_recipes(self, recipes: List[dict], user_approval: bool = False) -> List[dict]:
        """
        Insert recipes only after explicit user approval.
        Returns a list of inserted recipes with IDs.
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

            # Dedup check
            if self.recipe_exists(recipe_name):
                skipped.append(recipe_name)
                continue

            # Normalize meal_type to string
            if isinstance(meal_type, list):
                meal_type = meal_type[0] if meal_type else None

            # ---------------- Insert recipe ----------------
            record = {
                "recipe_name": recipe_name,
                "ingredients": ingredients,
                "instructions": instructions,
                "recipe_date": recipe_date,
                "link": link,
                "meal_type": meal_type,
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
