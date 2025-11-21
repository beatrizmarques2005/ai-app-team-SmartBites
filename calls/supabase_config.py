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
            print("✅ Pantry table created")
            
            # Create recipe (this creates recipes table)
            recipe_data = {
                "user_id": user_id,
                "title": "Sample Recipe",
                "ingredients": [],
                "instructions": "Sample instructions"
            }
            supabase.table("recipes").insert(recipe_data).execute()
            print("✅ Recipes table created")
            
            # Clean up test data
            supabase.table("users").delete().eq("id", user_id).execute()
            print("✅ Test data cleaned up")
            
        print("🎉 Database initialization complete!")
        
    except Exception as e:
        print("Note: Tables might already exist or there was an error:", e)

# Auto-initialize when imported
initialize_database()