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

    def remove_item(self, item_id: int) -> None:
        """
        Remove a pantry item by its ID.

        Args:
            item_id: The ID of the pantry item to remove.
        """
        supabase.table("pantry_items").delete().eq("id", item_id).eq("user_id", self.user_id).execute()
    
    @observe()
    def consume_items(self, ingredients: List[dict]) -> None:
        """
        Consume ingredients from the pantry when a recipe is approved.
        Prioritizes oldest purchases first (FIFO).

        Args:
            ingredients: List of dicts with keys:
                - ingredient_name (str)
                - quantity (float/int)
        """
        for ing in ingredients:
            name = ing["ingredient_name"]
            qty_needed = ing["quantity"]

            # Fetch pantry items for this ingredient, ordered by purchase_date (oldest first)
            res = supabase.table("pantry_items") \
                .select("*") \
                .eq("user_id", self.user_id) \
                .eq("ingredient_name", name) \
                .order("purchase_date", ascending=True) \
                .execute()

            pantry_items = res.data

            if not pantry_items:
                continue  # No stock, maybe log warning

            for item in pantry_items:
                if qty_needed <= 0:
                    break

                available_qty = item["quantity"]

                if available_qty <= qty_needed:
                    # Consume entire item
                    supabase.table("pantry_items").delete().eq("id", item["id"]).execute()
                    qty_needed -= available_qty
                else:
                    # Partially consume
                    new_qty = available_qty - qty_needed
                    supabase.table("pantry_items").update({"quantity": new_qty}).eq("id", item["id"]).execute()
                    qty_needed = 0
