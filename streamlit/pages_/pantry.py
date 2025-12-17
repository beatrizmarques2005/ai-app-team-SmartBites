import streamlit as st
import sys
import os
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.db.client import supabase
from src.authentication import AuthService

def pantry_page():
    st.set_page_config(page_title="Pantry", page_icon="🥫", layout="wide", initial_sidebar_state='collapsed' )
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

        search_query = st.text_input("Search infredients...")
        if search_query:
            pantry_items = [item for item in pantry_items if search_query.lower() in item['ingredient_name'].lower()]

        if not pantry_items:
            st.info("Your pantry is empty.")
        else:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                    col_a.markdown("**Ingredient**")
            with col_b:
                    col_b.markdown("**Quantity**")
            with col_c:
                    col_c.markdown("**Added On**")
            for item in pantry_items:
                col_a.markdown(f"{item['ingredient_name']}")
                col_b.markdown(f"{item['quantity']}")
                col_c.markdown(f"{item['purchase_date']}")
                
                # date_obj = datetime.fromisoformat(item["purchase_date"])
                # formatted_date = date_obj.strftime("%d %B")

                # st.markdown(
                #     f"""
                #     **{item['ingredient_name']}**  
                #     Quantity: {item['quantity']}  
                #     Added on: {item['purchase_date']}
                #     """
                # )
                # st.divider()

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
                    f"{item['ingredient']} ({item['quantity']})",
                    key=item["id"]
                )

                if checked:
                    supabase.table("shopping_list")\
                        .delete()\
                        .eq("id", item["id"])\
                        .execute()

                    st.rerun()