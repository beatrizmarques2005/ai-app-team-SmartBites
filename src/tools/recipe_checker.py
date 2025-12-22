"""
Recipe Checker Module
---------------------

Inspect previously cooked recipes to avoid repetition.

"""

from typing import List
from datetime import datetime, timedelta
from langfuse import observe

from src.authentication import AuthService
from src.db.client import supabase

class RecipeChecker:
    """Inspect previously cooked recipes to avoid repetition."""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()

    @observe()
    def _fetch_recent_recipes(self, weeks: int):
        """
        Fetches recent recipes for the user within a specified number of weeks.
        Args:
            weeks (int): The number of weeks to look back for recent recipes.
        Returns:
            result: A list of recipes that match the criteria, or None if the user_id is not set.

        The function retrieves recipes from the 'recipes' table in the Supabase database,
        filtering by the user's ID and the meal date, which must be greater than or equal
        to the cutoff date calculated from the current date minus the specified number of weeks.
        The results are ordered by meal date in descending order.
        """

        if not self.user_id:
            return None

        today = datetime.utcnow().date()
        cutoff = today - timedelta(weeks=weeks)

        result = (
            supabase.table("recipes")
            .select("recipe_name,meal_date,meal_type,link")
            .eq("user_id", self.user_id)
            .gte("meal_date", cutoff.isoformat())
            .order("meal_date", desc=True)
            .execute()
        )
        return result

    @observe()
    def recent_recipes(self, weeks: int = 3) -> str:
        """
        Retrieve a list of recent recipes from the past specified number of weeks.
        Args:
            weeks (int): The number of weeks to look back for recent recipes. Default is 3.
        Returns:
            str: A comma-separated string of recipe names along with their meal dates in the format 'YYYY-MM-DD'.
                 Returns an empty string if no recent recipes are found.
        """
        res = self._fetch_recent_recipes(weeks=weeks)
        if not res or not res.data:
            return ""

        parts = []
        for row in res.data:
            name = row.get("recipe_name", "Unknown")
            date = row.get("meal_date", "")
            if date:
                date = date.split("T")[0]
            parts.append(f"{name.lower()} ({date})")

        return ", ".join(parts)

    @observe()
    def recent_recipe_names(self, weeks: int = 3) -> List[str]:
        """
        Retrieve the names of recent recipes added within a specified number of weeks.
        Args:
            weeks (int): The number of weeks to look back for recent recipes. Defaults to 3.
        Returns:
            List[str]: A list of recipe names that were added within the specified time frame.
                        Returns an empty list if no recent recipes are found or if the data is not available.
        """
        res = self._fetch_recent_recipes(weeks=weeks)
        if not res or not res.data:
            return []

        return [r.get("recipe_name") for r in res.data if r.get("recipe_name")]
