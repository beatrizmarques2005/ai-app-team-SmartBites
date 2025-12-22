"""
Pantry page for the SmartBites Streamlit app.

Purpose:
- Display and manage the user's pantry items (view, search, adjust, remove).
- Persist changes to quantities and deletions in the Supabase `pantry_items` table.

UI Flow:
- Configures the page (title, icon, wide layout, collapsed sidebar).
- Reads `user_id` from `st.session_state` and queries `pantry_items` for that user.
- Sorts results by `purchase_date` then `id`, supports text search by ingredient name.
- Renders a table-like layout with columns for ingredient, date, quantity, adjust, and remove.
- Increment/decrement buttons update quantity; zero quantity triggers deletion.
- A checkbox allows removing an item directly.

Session State Keys:
- `auth`: `AuthService` instance used to resolve `user_id`.
- `user_id`: identifies the current user; required for reads/writes.
- Per-row component keys: `dec_<id>_<idx>`, `inc_<id>_<idx>`, `remove_<id>_<idx>` to ensure stable widget state.

Database Schema:
- Operates on `pantry_items` with fields `id`, `user_id`, `ingredient_name`, `purchase_date`, `quantity`.

Entry Point:
- `pantry_page()`: renders the pantry UI and handles Supabase CRUD operations.
"""
import streamlit as st
from langfuse import observe
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.db.client import supabase
from src.authentication import AuthService

@observe
def pantry_page():
    st.set_page_config(
        page_title="Pantry",
        page_icon="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/basket.svg",
        layout="wide",
        initial_sidebar_state='collapsed'
    )
    st.title("My Pantry")
    st.write("Manage your pantry items here! You can adjust quantities or remove items as needed.")
    st.markdown("")
    auth = st.session_state.auth
    user_id = st.session_state.get('user_id', None) or auth.get_user_id()

    if "auth" not in st.session_state:
        st.session_state.auth = AuthService()

    if not user_id:
        st.warning("User not logged in properly.")
        st.stop()

    pantry_response = supabase.table("pantry_items")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("purchase_date", desc=False)\
        .execute()

    pantry_items = sorted(
        pantry_response.data or [],
        key=lambda i: ((i.get('purchase_date') or ''), (i.get('id') or 0))
    )

    # Search for items
    search_query = st.text_input("Search ingredients...")
    if search_query:
        pantry_items = [item for item in pantry_items if search_query.lower() in item['ingredient_name'].lower()]

    if not pantry_items:
        st.info("Your pantry is empty.")

    else:
        # Table header
        header_cols = st.columns([2, 1.5, 1.5, 1, 0.8])
        header_cols[0].markdown("<div style='text-align: center'><strong>Ingredient</strong></div>", unsafe_allow_html=True)
        header_cols[1].markdown("<div style='text-align: center'><strong>Purchased On</strong></div>", unsafe_allow_html=True)
        header_cols[2].markdown("<div style='text-align: center'><strong>Quantity</strong></div>", unsafe_allow_html=True)
        header_cols[3].markdown("<div style='text-align: center'><strong>Adjust</strong></div>", unsafe_allow_html=True)
        header_cols[4].markdown("<div style='text-align: center'><strong>Remove</strong></div>", unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 0.1rem 0; border: 0.5px solid #e0e0e0;' />", unsafe_allow_html=True)
        
        # Display each item as a row
        for idx, item in enumerate(pantry_items):
            row_cols = st.columns([2, 1.5, 1.5, 1, 0.8])
            
            # Ingredient
            row_cols[0].markdown(f"<div style='text-align: center'>{item['ingredient_name']}</div>", unsafe_allow_html=True)
            
            # Date
            row_cols[1].markdown(f"<div style='text-align: center'>{item['purchase_date']}</div>", unsafe_allow_html=True)
            
            # Quantity
            row_cols[2].markdown(f"<div style='text-align: center'>{item['quantity']}</div>", unsafe_allow_html=True)
            
            # Adjust quantity (+/-)
            item_id = item.get('id')
            manage_key_dec = f"dec_{item_id}_{idx}"
            manage_key_inc = f"inc_{item_id}_{idx}"
            
            adj_cols = row_cols[3].columns([1, 1], gap="small")
            if adj_cols[0].button(":material/remove:", key=manage_key_dec, use_container_width=True, type = "tertiary"):
                if item_id is None:
                    st.warning("Cannot update: missing id")
                else:
                    try:
                        new_quantity = max(0, item['quantity'] - 1)
                        supabase.table("pantry_items").update({"quantity": new_quantity}).eq("id", item_id).eq("user_id", user_id).execute()
                        if new_quantity == 0:
                            supabase.table("pantry_items").delete().eq("id", item_id).eq("user_id", user_id).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
            
            if adj_cols[1].button(":material/add:", key=manage_key_inc, use_container_width=True, type="tertiary"):
                if item_id is None:
                    st.warning("Cannot update: missing id")
                else:
                    try:
                        new_quantity = item['quantity'] + 1
                        supabase.table("pantry_items").update({"quantity": new_quantity}).eq("id", item_id).eq("user_id", user_id).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
            
            # Remove checkbox
            remove_key = f"remove_{item_id}_{idx}"
            with row_cols[4]:
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    remove_checked = st.checkbox("", key=remove_key)
            if remove_checked:
                if item_id is None:
                    st.warning("Cannot remove: missing id")
                else:
                    try:
                        supabase.table("pantry_items").delete().eq("id", item_id).eq("user_id", user_id).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
            
            st.markdown("<hr style='margin: 0.1rem 0; border: 0.5px solid #e0e0e0;' />", unsafe_allow_html=True)

