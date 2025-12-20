import logging
from typing import List, Dict, Optional, TypedDict
from langfuse import observe
from src.authentication import AuthService
from src.db.client import supabase

logger = logging.getLogger(__name__)

class ShoppingItem(TypedDict):
    ingredient_name: str
    quantity: float

class ShoppingListWriter:
    
    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if not self.user_id:
            raise ValueError("User must be authenticated.")

    """@observe()
    def add_shopping_items(
        self,
        items, #List[ShoppingItem],
        user_approval: bool = False,
        merge_if_exists: bool = True,
    ) -> Dict[str, list]:
        '''
        Adds multiple items to the shopping list. 
        Expected format for 'items': [{"ingredient_name": "apple", "quantity": 2}, ...]
        '''
        #if not user_approval:
        #    logger.info("Operation aborted: User approval required.")
        #    return {"inserted": [], "updated": [], "skipped": []}

        # Safety Check: Ensure 'items' is a list to prevent 'AddShoppingItemsItems' errors
        if isinstance(items, dict):
            items = [items]
        
        if not isinstance(items, list):
            logger.error(f"Invalid input: expected list of items, got {type(items)}")
            return {
                "error": "Invalid input format",
                "inserted": [], "updated": [], "skipped": []}

        # 1. Pre-fetch all current items to avoid N+1 queries
        try:
            current_list_res = (
                supabase.table("shopping_list")
                .select("id", "ingredient_name", "quantity")
                .eq("user_id", self.user_id)
                .execute()
            )
            existing_map = {row["ingredient_name"]: row for row in current_list_res.data}
        except Exception as e:
            logger.error(f"Database error during pre-fetch: {e}")
            return {"inserted": [], "updated": [], "skipped": [], "error": str(e)}

        results = {"inserted": [], "updated": [], "skipped": []}
        to_insert = []

        for item in items:

            if not isinstance(item, dict):
                logger.error(f"Invalid item type: {type(item)}")
                continue
            # Handle potential missing keys if LLM sends malformed dicts
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
                    "ingredient_name": name,
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
        
        if not results["inserted"] and not results["updated"]:
            logger.warning("Shopping list update resulted in no changes")

        return results"""
    
import logging
from typing import List, Dict
from langfuse import observe
from src.authentication import AuthService
from src.db.client import supabase

logger = logging.getLogger(__name__)


class ShoppingListWriter:
    """Original class to interact with the database"""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if not self.user_id:
            raise ValueError("User must be authenticated.")

    def add_shopping_items(self, items: list, merge_if_exists=True) -> dict:
        """
        Internal method to add items to the shopping list.

        items: list of dicts {"ingredient_name": str, "quantity": float}
        merge_if_exists: whether to merge quantities if item exists
        """
        results = {"inserted": [], "updated": [], "skipped": [], "error": None}

        if isinstance(items, dict):
            items = [items]

        if not isinstance(items, list):
            results["error"] = f"Invalid input type: {type(items)}. Expected list or dict."
            return results

        # Fetch existing shopping list
        try:
            current_list_res = (
                supabase.table("shopping_list")
                .select("id", "ingredient_name", "quantity")
                .eq("user_id", self.user_id)
                .execute()
            )
            existing_map = {row["ingredient_name"]: row for row in current_list_res.data}
        except Exception as e:
            results["error"] = f"Database error during pre-fetch: {e}"
            return results

        to_insert = []

        for item in items:
            if not isinstance(item, dict):
                continue

            name = item.get("ingredient_name")
            qty = item.get("quantity", 1)

            if not name:
                continue

            name = str(name).strip().lower()
            try:
                qty = float(qty)
            except (TypeError, ValueError):
                qty = 1.0

            # Update existing item
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
                        results["error"] = f"Error updating {name}: {e}"
                else:
                    results["skipped"].append(name)
            # Insert new item
            else:
                to_insert.append({
                    "ingredient_name": name,
                    "quantity": qty,
                    "user_id": self.user_id
                })

        # Bulk insert
        if to_insert:
            try:
                res = supabase.table("shopping_list").insert(to_insert).execute()
                if res.data:
                    results["inserted"].extend(res.data)
            except Exception as e:
                results["error"] = f"Error during bulk insert: {e}"

        return results

    def remove_item(self, item_id: int) -> bool:
        """Remove a single item from the shopping list."""
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


# =========================
# LLM-friendly wrapper
# =========================

@observe()
def add_shopping_items_llm(items):
    """
    LLM-friendly wrapper for automatic function calling.

    items: single dict or list of dicts
        Each dict should contain:
            - ingredient_name: str
            - quantity: float (optional, default 1)
            - merge_if_exists: bool (optional, default True)
    """
    if isinstance(items, dict):
        items = [items]

    # Extract merge_if_exists flags from items
    merge_if_exists = True
    for item in items:
        if "merge_if_exists" in item:
            merge_if_exists = bool(item.pop("merge_if_exists"))

    writer = ShoppingListWriter(auth=AuthService())
    return writer.add_shopping_items(items, merge_if_exists=merge_if_exists)

    