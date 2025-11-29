"""ShoppingListService - manage shopping list items via SupabaseAdapter."""
from typing import List, Optional, Dict, Any
from ..db.supabase_adapter import SupabaseAdapter
from ..utils.text_normalization import normalize_text


class ShoppingListService:
    def __init__(self):
        self.adapter = SupabaseAdapter()

    def list_items(self, user_id: str) -> List[Dict[str, Any]]:
        resp = self.adapter.client.table("shopping_list_items").select("*").eq("user_id", user_id).execute()
        return getattr(resp, 'data', []) or []

    def add_item(self, user_id: str, name: str, quantity: Optional[float] = None, unit: Optional[str] = None, section: Optional[str] = None, auto_added_by: Optional[str] = None) -> Dict[str, Any]:
        normalized = normalize_text(name)
        payload = {
            "user_id": user_id,
            "name": name,
            "normalized_name": normalized,
            "quantity": quantity,
            "unit": unit,
            "section": section,
            "auto_added_by": auto_added_by,
        }
        resp = self.adapter.client.table("shopping_list_items").insert(payload).execute()
        if getattr(resp, 'data', None):
            return resp.data[0]
        return {}

    def remove_item(self, user_id: str, item_id: str) -> bool:
        resp = self.adapter.client.table("shopping_list_items").delete().eq("id", item_id).eq("user_id", user_id).execute()
        return getattr(resp, 'status_code', None) in (200,204) or (getattr(resp,'data',None) is not None)
