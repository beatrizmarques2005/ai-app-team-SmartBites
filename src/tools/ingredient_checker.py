import json
from typing import Optional
from langfuse import observe
from src.services.auth_service import AuthService
from src.db.client import supabase


class IngredientChecker:
    """Check pantry_items and suggest AI-based replacements."""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if self.user_id:
            self.pantry_items = supabase.table("pantry_items").select('*').eq('user_id', self.user_id).execute()
        else:
            self.pantry_items = None

    def available_ingredients(self) -> Optional[str]:
        """
        Return a human-friendly, comma-separated summary of available pantry ingredients and their quantities.
        This method normalizes different shapes of self.pantry_items (e.g., a Supabase response object with a .data
        attribute, a dict with a "data" key, or a raw iterable of rows) and builds a readable string describing
        each pantry item. Each row is expected to contain common field names; when present the method uses:
        - "ingredient_name" for the item name
        - "quantity" for the item's amount
        Behavior:
        - If self.pantry_items is falsy or contains no rows, an empty string is returned.
        - For each row:
            - If "ingredient_name" exists, it is used as the displayed name; otherwise the entire row is JSON-stringified
                (json.dumps) and, if that fails, converted with str(row).
            - If "quantity" exists, the entry is formatted as "name: quantity"; otherwise just "name".
        - Entries are joined with ", " to form the final summary string.
        Parameters
        ----------
        ingredient : str
                Present for API compatibility but not used by the current implementation. Intended for future
                filtering or lookup by a specific ingredient name.
        Returns
        -------
        Optional[str]
                A comma-separated summary string of pantry_items items (e.g. "Salt: 2g, Sugar: 1kg") or an empty string
                if no pantry_items/rows are available.
        Notes
        -----
        - The method expects rows to be mapping-like (supporting .get). If rows contain non-mapping values, the
            fallback stringification will still include them.
        - The function uses json.dumps to produce readable fallbacks for complex row objects; ensure the json
            module is available in the module namespace.
        Examples
        --------
        Assuming self.pantry_items resolves to:
        [{"ingredient_name": "Flour", "quantity": "2kg"}, {"ingredient_name": "Eggs"}]
        The return value will be:
        "Flour: 2kg, Eggs"
        """

        # Build a friendly string of all pantry items and their quantities.
        if not self.pantry_items:
            return ""

        # Normalize supabase response (it may be a dict with "data" or an object with .data)
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
            created = r.get("created_at")

            entry = name
            if qty:
                entry += f": {qty}"
            if created:
                entry += f" (added on {created})"

            parts.append(entry)

        return ", ".join(parts)
