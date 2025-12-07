import json
from datetime import datetime
from typing import Optional, List
from langfuse import observe

from src.authentication import AuthService
from src.db.client import supabase


class PantryWriter:
    """Insert parsed pantry items based on AI understanding."""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if not self.user_id:
            raise ValueError("User must be authenticated to add pantry items.")

    @observe()  # Traces to Langfuse
    def add_items(self, items: List[dict]) -> str:
        """
        Insert multiple pantry items into the database.

        Each item dict may include:
            - ingredient_name (required)
            - quantity (required)
            - store_name (optional)
            - purchase_date (optional)

        If purchase_date are not provided, they default to now (UTC).

        Returns:
            A friendly confirmation string summarizing what was inserted.
        """
        inserted = []

        for i in items:
            ingredient_name = i.get("ingredient_name")
            quantity = i.get("quantity")
            store_name = i.get("store_name")

            purchase_date = i.get("purchase_date")

            if purchase_date is None:
                purchase_date = datetime.utcnow().date().isoformat()

            record = {
                "ingredient_name": ingredient_name,
                "quantity": quantity,
                "store_name": store_name,
                "purchase_date": purchase_date,
                "user_id": self.user_id,
            }

            res = supabase.table("pantry_items").insert(record).execute()
            inserted.append(record)

        # ------- Confirmation Text -------
        readable = []
        for r in inserted:
            readable.append(f"{r['quantity']} {r['ingredient_name']}")
        return "Added to pantry: " + ", ".join(readable)

