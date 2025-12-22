"""
Shopping List Writer Module
---------------------------

This module provides functionality to add, update, and remove items
from a user's shopping list in the database. It ensures efficient
database operations by minimizing the number of queries executed.

"""

import logging
from typing import List, Dict, TypedDict
from langfuse import observe

from src.authentication import AuthService
from src.db.client import supabase

logger = logging.getLogger(__name__)

class ShoppingItem(TypedDict):
    """
    A typed dictionary representing a shopping item.

    Attributes:
        ingredient_name (str): The name of the ingredient to be purchased.
        quantity (float): The amount or quantity of the ingredient needed.
    """
    ingredient_name: str
    quantity: float

class ShoppingListWriter:
    
    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if not self.user_id:
            raise ValueError("User must be authenticated.")

    @observe()
    def add_shopping_items(
        self,
        items: List[Dict[str, object]],
        user_approval: bool = True,
        merge_if_exists: bool = True,
    ) -> Dict[str, list]:
        
        """
        Add or update shopping list items for the current user.
        This method processes a list of shopping items and either inserts new items
        or updates existing ones based on the ingredient name. It optimizes database
        operations by pre-fetching all current items to avoid N+1 queries and uses
        bulk insert for new items.
        Args:
            items (List[Dict[str, object]]): A list of dictionaries containing shopping items.
                Each dictionary should have the following keys:
                - "ingredient_name" (str): The name of the ingredient (required).
                - "quantity" (int, optional): The quantity to add. Defaults to 1.
            user_approval (bool, optional): Whether the user has approved this operation.
                Defaults to True. If False, the operation is aborted.
            merge_if_exists (bool, optional): Whether to merge quantities if an ingredient
                already exists in the shopping list. Defaults to True. If False, existing
                items are skipped.
        Returns:
            Dict[str, list]: A dictionary containing the operation results with the
                following keys:
                - "inserted" (list): Successfully inserted shopping list items.
                - "updated" (list): Successfully updated shopping list items.
                - "skipped" (list): Items that were skipped because they already exist
                  and merge_if_exists is False.
                - "error" (str, optional): Error message if an exception occurs during
                  database operations.
        Raises:
            None. Exceptions are caught and logged, with errors returned in the result dictionary.
        """

        if not user_approval:
            logger.info("Operation aborted: User approval required.")
            return {"inserted": [], "updated": [], "skipped": []}

        if not isinstance(items, list):
            logger.error(f"Invalid input: expected list of items, got {type(items)}")
            return {"inserted": [], "updated": [], "skipped": [], "error": "Invalid input format"}

        # 1. Pre-fetch all current items to avoid N+1 queries
        try:
            current_list_res = (
                supabase.table("shopping_list")
                .select("id", "ingredient_name", "quantity")
                .eq("user_id", self.user_id)
                .execute()
            )
            existing_map = {row["ingredient_name"].lower(): row for row in current_list_res.data}
        except Exception as e:
            logger.error(f"Database error during pre-fetch: {e}")
            return {"inserted": [], "updated": [], "skipped": [], "error": str(e)}

        results = {"inserted": [], "updated": [], "skipped": []}
        to_insert = []

        for item in items:
            name = item.get("ingredient_name")
            qty = item.get("quantity", 1)
            
            if not name:
                continue

            if name in existing_map:
                if merge_if_exists:
                    new_qty = (existing_map[name].get("quantity") or 0) + qty
                    try:
                        res = (
                            supabase.table("shopping_list")
                            .update({"quantity": new_qty})
                            .eq("id", existing_map[name]["id"])
                            .execute()
                        )
                        if res.data:
                            results["updated"].append(res.data[0])
                    except Exception as e:
                        logger.error(f"Error updating {name}: {e}")
                else:
                    results["skipped"].append(name)
            else:
                to_insert.append({
                    "ingredient_name": name.lower(),
                    "quantity": qty,
                    "user_id": self.user_id
                })

        # 2. Bulk Insert new items
        if to_insert:
            try:
                res = supabase.table("shopping_list").insert(to_insert).execute()
                if res.data:
                    results["inserted"].extend(res.data)
            except Exception as e:
                logger.error(f"Error during bulk insert: {e}")

        return results

    @observe()
    def remove_item(self, item_id: int) -> bool:
        """
        Remove an item from the shopping list.
        
        Args:
            item_id (int): The unique identifier of the item to remove.
        
        Returns:
            bool: True if the item was successfully deleted, False otherwise.
        
        Raises:
            None: Exceptions are caught and logged internally.
        """
        try:
            res = (
                supabase.table("shopping_list")
                .delete()
                .eq("id", item_id)
                .eq("user_id", self.user_id)
                .execute()
            )
            return len(res.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete item {item_id}: {e}")
            return False
        