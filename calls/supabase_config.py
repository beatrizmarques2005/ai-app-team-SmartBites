from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("✅ Supabase client created successfully!")

def initialize_database():
    """Create all tables if they don't exist"""
    print("🔄 Initializing database tables...")
    
    try:
        # This will automatically create tables when we insert data
        # Create a test user (this creates users table)
        test_user = {
            "email": "setup@example.com",
            "username": "setupuser",
            "name": "Setup User"
        }
        
        result = supabase.table("users").insert(test_user).execute()
        if result.data:
            user_id = result.data[0]["id"]
            print("✅ Users table created")
            
            # Create pantry (this creates pantry table)
            pantry_data = {
                "user_id": user_id,
                "items": []
            }
            supabase.table("pantry").insert(pantry_data).execute()
            """
            Deprecated compatibility shim for older imports.

            This module re-exports the centralized Supabase client from `src.db.client` so
            existing code that imports `calls.supabase_config` keeps working. It intentionally
            does NOT perform any schema modifications or insert test rows.

            If you need to initialize or migrate the database, run the SQL in
            `src/db/migrations/001_init.sql` via the Supabase SQL editor or add a migration
            runner that uses a service role key.
            """

            from src.db.client import supabase

            __all__ = ["supabase"]



# INSERTS IN THE TABLES
def insert_receipt_into_pantry(user_id: str, receipt_json: dict):
    """
    Takes JSON from OCR-extracted receipt and inserts items into pantry_items table.
    """

    store_name = receipt_json.get("store_name")
    purchase_date = receipt_json.get("purchase_date")
    purchase_time = receipt_json.get("purchase_time")
    items = receipt_json.get("items", [])

    rows_to_insert = []

    for item in items:
        rows_to_insert.append({
            "user_id": user_id,
            "item_name": item.get("name"),
            "quantity": item.get("quantity", 1),
            "store_name": store_name,
            "purchase_date": purchase_date,
            "purchase_time": purchase_time,
        })

    # Insert all items at once
    response = supabase.table("pantry_items").insert(rows_to_insert).execute()

    return response

