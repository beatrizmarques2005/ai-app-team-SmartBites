
from typing import Optional, List
from datetime import datetime, timedelta
from langfuse import observe

from src.authentication import AuthService
from src.db.client import supabase


class RecipeChecker:
    """Inspect previously cooked recipes to avoid repetition."""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()

    def _fetch_recent_recipes(self, weeks: int):
        """
        Internal helper: fetch recipes from the last X weeks using meal_date.
        """
        if not self.user_id:
            return None

        today = datetime.utcnow().date()
        cutoff = today - timedelta(weeks=weeks)

        result = (
            supabase.table("recipes")
            .select("recipe_name,meal_date,meal_type,link")
            .eq("user_id", self.user_id)
            .gte("meal_date", cutoff.isoformat())    # filter
            .order("meal_date", desc=True)
            .execute()
        )
        return result

    @observe()
    def recent_recipes(self, weeks: int = 3) -> str:
        """
        Return a friendly string summary of recipes cooked in the last X weeks.

        Output example:
        "Pasta Carbonara (2025-02-09), Tuna Rice (2025-02-07)"
        """
        res = self._fetch_recent_recipes(weeks=weeks)
        if not res or not res.data:
            return ""

        parts = []
        for row in res.data:
            name = row.get("recipe_name", "Unknown")
            date = row.get("meal_date", "")
            if date:
                date = date.split("T")[0]  # normalize YYYY-MM-DD
            parts.append(f"{name} ({date})")

        return ", ".join(parts)

    @observe()
    def recent_recipe_names(self, weeks: int = 3) -> List[str]:
        """
        Return ONLY the recipe names list,
        ideal to avoid recommending recipes similar to recent ones.
        """
        res = self._fetch_recent_recipes(weeks=weeks)
        if not res or not res.data:
            return []

        return [r.get("recipe_name") for r in res.data if r.get("recipe_name")]
