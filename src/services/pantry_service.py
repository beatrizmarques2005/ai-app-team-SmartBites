"""PantryService - manage pantry items via SupabaseAdapter."""
from typing import List, Optional, Dict, Any
from ..db.supabase_adapter import SupabaseAdapter
from ..utils.text_normalization import normalize_text
from ..utils.unit_conversion import convert_to_base, to_pretty
from ..tools.date_calculator import get_food_status


class PantryService:
    def __init__(self, adapter: Optional[SupabaseAdapter] = None):
        """PantryService manages pantry items.

        Args:
            adapter: Optional SupabaseAdapter or mock for testing. If None, a real adapter is created.
        """
        self.adapter = adapter or SupabaseAdapter()

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

    def expiry_check(self, user_id: str) -> Dict[str, dict]:
        """Return a mapping of normalized item name -> item data merged with expiry info.

        Uses `open_date` (DD-MM-YYYY) and `shelf_life` (days) fields when available.
        If those fields are missing the item will be included with status 'Unknown'.
        """
        items = self.list_items(user_id)
        status = {}
        for row in items:
            try:
                qty = row.get('quantity') or 0
            except Exception:
                qty = 0
            if qty <= 0:
                continue

            name = row.get('normalized_name') or normalize_text(row.get('name', ''))
            open_date = row.get('open_date')
            shelf_life = row.get('shelf_life')

            if not open_date or not shelf_life:
                expiry = {
                    'open_date': open_date,
                    'expire_date': None,
                    'days_remaining': 9999,
                    'status': 'Unknown'
                }
            else:
                try:
                    expiry = get_food_status(open_date, int(shelf_life))
                except Exception:
                    expiry = {
                        'open_date': open_date,
                        'expire_date': None,
                        'days_remaining': 9999,
                        'status': 'Unknown'
                    }

            status[name] = {**row, **expiry}

        return status

    def get_ingredients_for_recipe(self, user_id: str, prioritize_expiring: bool = True) -> List[str]:
        """Return a list of ingredient names suitable for recipe generation.

        Items are sorted by `days_remaining` when `prioritize_expiring` is True.
        Expired items are filtered out.
        """
        items = self.expiry_check(user_id)
        sorted_items = sorted(
            items.items(),
            key=lambda x: x[1].get('days_remaining', 9999) if prioritize_expiring else 0
        )

        return [name for name, data in sorted_items if data.get('status') != 'Expired' and (data.get('quantity') or 0) > 0]
