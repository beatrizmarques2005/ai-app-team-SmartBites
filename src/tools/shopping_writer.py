
from typing import List
from langfuse import observe
from src.authentication import AuthService
from src.db.client import supabase


class ShoppingListWriter:
    """Insert or update shopping list items, respecting duplicates."""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if not self.user_id:
            raise ValueError("User must be authenticated.")

    # ---------------- Check if item exists ----------------
    def item_exists(self, ingredient_name: str) -> dict | None:
        """Return the existing row if present, otherwise None."""
        res = (
            supabase.table("shopping_list")
            .select("*")
            .eq("user_id", self.user_id)
            .eq("ingredient_name", ingredient_name)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    # ---------------- Add Items ----------------
    @observe()
    def add_shopping_items(
        self,
        items: List[dict],
        user_approval: bool = False,
        merge_if_exists: bool = True,
    ) -> dict:
        """
        Insert items to shopping_list, respecting duplicates.

        Parameters
        ----------
        items : [{ingredient_name, quantity}]
        user_approval : bool
            Insert only after explicit approval.
        merge_if_exists : bool
            If True: increase quantity on duplicate.
            If False: skip duplicates.

        Returns
        -------
        dict: {inserted:[...], updated:[...], skipped:[...]}
        """

        if not user_approval:
            print("Not inserted — waiting for explicit approval.")
            return {"inserted": [], "updated": [], "skipped": []}

        inserted, updated, skipped = [], [], []

        for obj in items:
            name = obj.get("ingredient_name")
            qty = obj.get("quantity") or 1

            if not name:
                print("Skipping entry: missing ingredient_name.")
                continue

            existing = self.item_exists(name)

            # ----------------------------------------------
            # Case 1 — item exists
            # ----------------------------------------------
            if existing:

                if merge_if_exists:
                    new_qty = (existing["quantity"] or 0) + qty
                    try:
                        supabase.table("shopping_list") \
                            .update({"quantity": new_qty}) \
                            .eq("id", existing["id"]) \
                            .execute()
                        updated.append({"id": existing["id"], "ingredient_name": name, "quantity": new_qty})
                        print(f"Updated '{name}' → quantity {new_qty}")
                    except Exception as e:
                        print(f"Error updating '{name}': {e}")

                else:
                    skipped.append(name)

                continue

            # ----------------------------------------------
            # Case 2 — fresh insert
            # ----------------------------------------------
            record = {
                "ingredient_name": name,
                "quantity": qty,
                "user_id": self.user_id,
            }

            try:
                res = (
                    supabase.table("shopping_list")
                    .insert(record, returning="representation")
                    .execute()
                )
            except Exception as e:
                print(f"Error inserting '{name}': {e}")
                continue

            if res.data and len(res.data) > 0:
                record["id"] = res.data[0]["id"]
                inserted.append(record)
                print(f"Added to shopping list: {name} (qty: {qty}, id: {record['id']})")
            else:
                print(f"Inserted '{name}' but no ID returned.")

        return {"inserted": inserted, "updated": updated, "skipped": skipped}
