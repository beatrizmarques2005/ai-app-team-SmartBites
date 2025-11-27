"""Quick script to test SupabaseAdapter connectivity.

Set `SUPABASE_URL` and `SUPABASE_KEY` in your `.env` before running.

How to run?
project-env\Scripts\activate
python .\scripts\test_supabase.py

"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `src` package is importable when running scripts
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db.supabase_adapter import SupabaseAdapter


def main():
    adapter = SupabaseAdapter()
    user_id = "test-user-local"
    receipt = {
        "store_name": "Local Test Store",
        "purchase_date": "2025-11-27",
        "items": [
            {"name": "milk", "quantity": 1, "unit": "L", "unit_price": 1.5},
            {"name": "eggs", "quantity": 12, "unit": "pcs", "unit_price": 2.5}
        ],
        "total": 4.0
    }

    print("Inserting test receipt...")
    r = adapter.insert_receipt(user_id, receipt)
    print("Inserted:", r)

    print("Upserting pantry item (milk)...")
    p = adapter.upsert_pantry_item(user_id, "milk", adapter._normalize_name("milk"), 1, "L", source_receipt_id=(r.get("id") if r else None))
    print("Pantry upsert result:", p)


if __name__ == "__main__":
    main()
