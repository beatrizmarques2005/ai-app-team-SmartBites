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

def shopping_list_page():
    st.set_page_config(page_title="Smartbites | Shopping list", page_icon="🥫", layout="wide", initial_sidebar_state='collapsed')
    st.title("My Shopping List")
    st.write("See your shopping list here and select an item to remove them from the list!")
    st.markdown("")
    st.markdown("")

    user_id = st.session_state.get('user_id', None)


    shopping_response = supabase.table("shopping_list")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()

    shopping_items = shopping_response.data

    search_query = st.text_input("Search ingredients...")
    if search_query:
        pantry_items = [item for item in pantry_items if search_query.lower() in item['ingredient_name'].lower()]

    st.markdown("")

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
