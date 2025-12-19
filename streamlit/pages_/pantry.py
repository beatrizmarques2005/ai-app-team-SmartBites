import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.db.client import supabase
from src.authentication import AuthService

def pantry_page():
    st.set_page_config(page_title="Pantry", page_icon="🥫", layout="wide", initial_sidebar_state='collapsed')
    st.title("My Pantry")
    st.write("Manage your pantry items here!")

    user_id = st.session_state.get('user_id', None)

    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("🧺 Pantry")


        pantry_response = supabase.table("pantry_items")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("purchase_date", desc=True)\
            .execute()

        pantry_items = pantry_response.data

        search_query = st.text_input("Search ingredients...")
        if search_query:
            pantry_items = [item for item in pantry_items if search_query.lower() in item['ingredient_name'].lower()]

        if not pantry_items:
            st.info("Your pantry is empty.")
        else:
            # Create table header
            header_cols = st.columns([2, 1.5, 1.5, 1, 0.8])
            header_cols[0].markdown("**Ingredient**")
            header_cols[1].markdown("**Added On**")
            header_cols[2].markdown("**Quantity**")
            header_cols[3].markdown("**Adjust**")
            header_cols[4].markdown("**Remove**")
            
            st.divider()
            
            # Display each item as a row with actions
            for idx, item in enumerate(pantry_items):
                row_cols = st.columns([2, 1.5, 1.5, 1, 0.8])
                
                # Ingredient
                row_cols[0].markdown(f"{item['ingredient_name']}")
                
                # Date
                row_cols[1].markdown(f"{item['purchase_date']}")
                
                # Quantity display
                row_cols[2].markdown(f"{item['quantity']}")
                
                # Adjust quantity (+/-)
                item_id = item.get('id')
                manage_key_dec = f"dec_{item_id}_{idx}"
                manage_key_inc = f"inc_{item_id}_{idx}"
                
                adj_cols = row_cols[3].columns([1, 1], gap="small")
                if adj_cols[0].button("-", key=manage_key_dec, use_container_width=True, type = "tertiary"):
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
                
                if adj_cols[1].button("➕", key=manage_key_inc, use_container_width=True, type="tertiary"):
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
                if row_cols[4].checkbox("", key=remove_key):
                    if item_id is None:
                        st.warning("Cannot remove: missing id")
                    else:
                        try:
                            supabase.table("pantry_items").delete().eq("id", item_id).eq("user_id", user_id).execute()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")

    with col2:
        st.header("🛒 Shopping List")

        shopping_response = supabase.table("shopping_list")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()

        shopping_items = shopping_response.data

        if not shopping_items:
            st.info("Your shopping list is empty.")
        else:
            for item in shopping_items:
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
    