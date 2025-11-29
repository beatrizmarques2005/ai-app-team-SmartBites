"""
Supabase adapter - small wrapper around the `supabase` client used by the project.

Responsibilities implemented here (small scope for POC):
- Insert receipts
- Upsert simple pantry items (aggregate quantity if exists)
- Remove / decrement shopping list items when a receipt contains purchased items

This file expects `calls/supabase_config.supabase` to provide a configured client.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from src.db.client import supabase


class SupabaseAdapter:
    def __init__(self):
        self.client = supabase

    def _normalize_name(self, name: str) -> str:
        if not name:
            return ""
        return name.strip().lower()

    def insert_receipt(self, user_id: str, receipt_data: dict) -> Optional[Dict[str, Any]]:
        payload = {
            "user_id": user_id,
            "store_name": receipt_data.get("store_name"),
            "purchase_date": receipt_data.get("purchase_date"),
            "purchase_time": receipt_data.get("purchase_time"),
            "invoice_number": receipt_data.get("invoice_number"),
            "items": receipt_data.get("items", []),
            "subtotal": receipt_data.get("subtotal"),
            "discounts": receipt_data.get("discounts"),
            "total": receipt_data.get("total"),
            "payment_method": receipt_data.get("payment_method"),
            "raw_ocr_text": receipt_data.get("raw_ocr_text"),
            "parsed": True,
            "parsing_confidence": receipt_data.get("parsing_confidence"),
            "created_at": datetime.utcnow().isoformat(),
        }

        resp = self.client.table("receipts").insert(payload).execute()
        if resp and hasattr(resp, "data") and resp.data:
            return resp.data[0]
        return None

    def find_pantry_item(self, user_id: str, normalized_name: str) -> Optional[Dict[str, Any]]:
        resp = self.client.table("pantry_items").select("*").eq("user_id", user_id).eq("normalized_name", normalized_name).limit(1).execute()
        if resp and getattr(resp, "data", None):
            return resp.data[0]
        return None

    def upsert_pantry_item(self, user_id: str, name: str, normalized_name: str, quantity: Optional[float], unit: Optional[str], source_receipt_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        existing = self.find_pantry_item(user_id, normalized_name)

        if existing:
            # Aggregate quantity when possible
            try:
                existing_qty = existing.get("quantity") or 0
                new_qty = (existing_qty or 0) + (quantity or 0)
            except Exception:
                new_qty = quantity

            update_doc = {
                "quantity": new_qty,
                "unit": unit or existing.get("unit"),
                "updated_at": datetime.utcnow().isoformat(),
            }
            resp = self.client.table("pantry_items").update(update_doc).eq("id", existing.get("id")).execute()
            if resp and getattr(resp, "data", None):
                return resp.data[0]
            return None

        # Create new pantry item
        payload = {
            "user_id": user_id,
            "name": name,
            "normalized_name": normalized_name,
            "quantity": quantity,
            "unit": unit,
            "source_receipt_id": source_receipt_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        resp = self.client.table("pantry_items").insert(payload).execute()
        if resp and getattr(resp, "data", None):
            return resp.data[0]
        return None

    def remove_shopping_list_item_if_present(self, user_id: str, normalized_name: str, quantity: Optional[float] = None):
        """If a shopping list item matches the purchased item, decrement or remove it.

        This is a best-effort operation for POC.
        """
        resp = self.client.table("shopping_list_items").select("*").eq("user_id", user_id).eq("normalized_name", normalized_name).limit(1).execute()
        if not resp or not getattr(resp, "data", None):
            return None

        item = resp.data[0]
        try:
            existing_qty = item.get("quantity") or 0
        except Exception:
            existing_qty = None

        if existing_qty is None or quantity is None:
            # Remove the item entirely
            self.client.table("shopping_list_items").delete().eq("id", item.get("id")).execute()
            return {"removed": True}

        # Decrement or delete
        new_qty = existing_qty - (quantity or 0)
        if new_qty <= 0:
            self.client.table("shopping_list_items").delete().eq("id", item.get("id")).execute()
            return {"removed": True}
        else:
            self.client.table("shopping_list_items").update({"quantity": new_qty}).eq("id", item.get("id")).execute()
            return {"updated_quantity": new_qty}
