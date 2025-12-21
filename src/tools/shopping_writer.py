import logging
from typing import List, Dict, Optional, TypedDict, Any
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

    @observe()
    def add_shopping_items(
        self,
        items: List[Dict[str, object]],
        user_approval: bool = True,
        merge_if_exists: bool = True,
    ) -> Dict[str, list]:
        """
        Adds multiple items to the shopping list. 
        Expected format for 'items': [{"ingredient_name": "apple", "quantity": 2}, ...]
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

        return results

    def remove_item(self, item_id: int) -> bool:
        """Removes item and returns success status."""
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
        