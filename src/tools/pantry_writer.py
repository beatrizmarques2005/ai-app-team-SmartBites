"""
Pantry Writer Module
--------------------

This module provides functionality to insert, remove, and consume pantry items
based on AI understanding and user authentication.

"""

from datetime import datetime
from typing import List
from langfuse import observe

from src.authentication import AuthService
from src.db.client import supabase


class PantryWriter:
    """Insert parsed pantry items based on AI understanding."""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if not self.user_id:
            raise ValueError("User must be authenticated to add pantry items.")

    @observe()
    def add_items(self, items: List[dict]) -> str:
        """
        Add multiple pantry items to the database.
        Args:
            items (List[dict]): A list of dictionaries containing pantry item details.
                Each dictionary should have the following keys:
                - ingredient_name (str): The name of the ingredient
                - quantity (str): The quantity of the ingredient
                - store_name (str): The store where the item was purchased
                - purchase_date (str, optional): The purchase date in ISO format.
                  If not provided, defaults to today's date.
                - user_id (str): The user ID (automatically added from self.user_id)
        Returns:
            str: A human-readable confirmation message listing all added items
                in the format "Added to pantry: <quantity> <ingredient_name>, ..."
        Raises:
            Exception: If the database insert operation fails.
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
                "store_name": store_name.lower() if store_name else None,
                "purchase_date": purchase_date,
                "user_id": self.user_id,
            }

            res = supabase.table("pantry_items").insert(record).execute()
            inserted.append(record)

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

            res = supabase.table("pantry_items") \
                .select("*") \
                .eq("user_id", self.user_id) \
                .eq("ingredient_name", name) \
                .order("purchase_date", ascending=True) \
                .execute()

            pantry_items = res.data

            if not pantry_items:
                continue

            for item in pantry_items:
                if qty_needed <= 0:
                    break

                available_qty = item["quantity"]

                if available_qty <= qty_needed:
                    supabase.table("pantry_items").delete().eq("id", item["id"]).execute()
                    qty_needed -= available_qty
                else:
                    new_qty = available_qty - qty_needed
                    supabase.table("pantry_items").update({"quantity": new_qty}).eq("id", item["id"]).execute()
                    qty_needed = 0
