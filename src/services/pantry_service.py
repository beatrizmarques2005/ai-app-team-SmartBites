"""PantryService - manage pantry items via SupabaseAdapter."""
from typing import List, Optional, Dict, Any
from ..db.supabase_adapter import SupabaseAdapter
from ..utils.text_normalization import normalize_text
from ..utils.unit_conversion import convert_to_base, to_pretty


class PantryService:
    def __init__(self):
        self.adapter = SupabaseAdapter()

    def list_items(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            resp = self.adapter.client.table("pantry_items").select("*").eq("user_id", user_id).execute()
            return getattr(resp, 'data', []) or []
        except AttributeError:
            # Fallback for simple test/mock adapters which store data on the adapter
            data = getattr(self.adapter, '_data', None)
            if data is None:
                return []
            return [r for r in data if r.get('user_id') == user_id]

    def add_or_update_item(self, user_id: str, name: str, quantity: Optional[float] = None, unit: Optional[str] = None, source_receipt_id: Optional[str] = None) -> Dict[str, Any]:
        normalized = normalize_text(name)
        # convert quantity to base for aggregation
        base_qty, base_unit = convert_to_base(quantity or 0, unit)
        item = self.adapter.upsert_pantry_item(user_id, name, normalized, base_qty, base_unit, source_receipt_id=source_receipt_id)
        return item

    def remove_item(self, user_id: str, item_id: str) -> bool:
        resp = self.adapter.client.table("pantry_items").delete().eq("id", item_id).eq("user_id", user_id).execute()
        return getattr(resp, 'status_code', None) in (200,204) or (getattr(resp,'data',None) is not None)

    def as_pretty(self, pantry_row: Dict[str, Any]) -> Dict[str, Any]:
        qty = pantry_row.get('quantity')
        unit = pantry_row.get('unit')
        if qty is None or unit is None:
            return pantry_row
        pretty_qty, pretty_unit = to_pretty(float(qty), unit)
        row = dict(pantry_row)
        row['pretty_quantity'] = pretty_qty
        row['pretty_unit'] = pretty_unit
        return row
