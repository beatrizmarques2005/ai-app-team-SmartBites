"""
Pantry Checker Module
---------------------

Check pantry_items and suggest AI-based replacements.

"""


from typing import Optional
from langfuse import observe

from src.authentication import AuthService
from src.db.client import supabase


class PantryChecker:
    """Check pantry_items and suggest AI-based replacements."""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if self.user_id:
            self.pantry_items = supabase.table("pantry_items").select('*').eq('user_id', self.user_id).execute()
        else:
            self.pantry_items = None

    @observe
    def available_ingredients(self) -> Optional[str]:
        """
        Retrieve a formatted string of available ingredients from the pantry.
        Returns a comma-separated string listing all ingredients currently in the pantry,
        including their quantities and purchase dates. Each ingredient entry follows the
        format: "{quantity} {ingredient_name} (added on {date})"
        The method handles multiple data structure formats:
        - Objects with a 'data' attribute
        - Dictionaries containing a 'data' key
        - Direct list/iterable structures
        Returns:
            Optional[str]: A formatted string of available ingredients with quantities and dates.
                           Returns an empty string if the pantry is empty or contains no items.
        Examples:
            "2 Tomatoes (added on 2024-01-15), 1 Milk (added on 2024-01-20)"
            "3 Eggs, 1 Flour (added on 2024-01-18)"
            "" (if pantry is empty)
        """

        if not self.pantry_items:
            return ""
        
        if hasattr(self.pantry_items, "data"):
            rows = self.pantry_items.data
        elif isinstance(self.pantry_items, dict) and "data" in self.pantry_items:
            rows = self.pantry_items["data"]
        else:
            rows = self.pantry_items

        if not rows:
            return ""

        parts = []
        for r in rows:
            name = r.get("ingredient_name", "Unknown")
            qty = r.get("quantity")
            created = r.get("purchase_date")

            entry = str(qty)
            if name:
                entry += f" {name}"
            if created:
                created = created.split("T")[0]
                entry += f" (added on {created})"

            parts.append(entry)

        return ", ".join(parts)
