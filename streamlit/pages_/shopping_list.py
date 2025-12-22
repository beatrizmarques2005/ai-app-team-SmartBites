"""
Shopping List page for the SmartBites Streamlit app.

Purpose:
- Display user's shopping list items with ingredient names and quantities.
- Allow users to mark items as purchased by checking them off (which removes them from the list).

UI Flow:
- Configures the page (title, icon, wide layout, collapsed sidebar).
- Queries the `shopping_list` table for all items belonging to the current user.
- Provides a search input to filter items by ingredient name.
- Displays each item as a checkbox with ingredient name and quantity.
- Checking a box deletes that item from the database.

Session State Keys:
- `auth`: `AuthService` instance used to resolve `user_id`.
- `user_id`: authenticated user identifier required for data scoping.

Database Schema:
- Reads from and deletes from `shopping_list` table with fields: `id` `user_id`, `ingredient_name`, `quantity`.

Entry Point:
- `shopping_list_page()`: renders shopping list UI and handles item deletion on checkbox interaction.
"""
import streamlit as st
from langfuse import observe
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.db.client import supabase
from src.authentication import AuthService

if "auth" not in st.session_state:
    st.session_state.auth = AuthService()

@observe
def shopping_list_page():
    st.set_page_config(
        page_title="Smartbites | Shopping list",
        page_icon="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/list-check.svg",
        layout="wide",
        initial_sidebar_state='collapsed'
    )
    st.title("My Shopping List")
    st.write("See your shopping list here and select an item to remove them from the list!")
    st.markdown("")
    st.markdown("")

    auth = st.session_state.auth
    user_id = st.session_state.get('user_id', None) or auth.get_user_id()

    if not user_id:
        st.warning("User not logged in properly.")
        st.stop()

    shopping_response = supabase.table("shopping_list")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()

    shopping_items = shopping_response.data

    # Search for items
    search_query = st.text_input("Search ingredients...")
    if search_query:
        pantry_items = [item for item in pantry_items if search_query.lower() in item['ingredient_name'].lower()]

    st.markdown("")

    # List shopping items
    if not shopping_items:
        st.info("Your shopping list is empty.")
    else:
        for item in shopping_items:
            # Checkbox to remove item from list
            checked = st.checkbox(
                f"{item['ingredient_name']} ({item['quantity']})",
                key=item["id"]
            )

            if checked:
                supabase.table("shopping_list")\
                    .delete()\
                    .eq("id", item["id"])\
                    .execute()
                
                st.rerun() 