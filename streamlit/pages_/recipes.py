import sys
import os

import streamlit as st

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.db.client import supabase
from src.authentication import AuthService

def recipes_page():
    st.set_page_config(page_title="Recipes", page_icon="🥫", layout="wide", initial_sidebar_state='collapsed' )
    st.title("My Recipes")
    st.write("See all your saved recipes here!")

    user_id = st.session_state.get('user_id', None)
    if not user_id:
        st.error("User not logged in.")
        return


    recipes_response = supabase.table("recipes")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("recipe_date", desc=True)\
            .execute()

    recipes = recipes_response.data
    if not recipes:
        st.info("No recipes found.")
        return


    if 'selected_recipe' not in st.session_state:
        st.session_state.selected_recipe = None
    #gallery view with 3 columns

    # Assuming `recipes` is a list of dicts
    cols = st.columns(3)

    for idx, recipe in enumerate(recipes):
        col = cols[idx % 3]  # rotate through columns
        with col:
            # st.markdown(
            #     f"""
            #     **{recipe['recipe_name']}**  
            #     {recipe['instructions']}  
            #     """
            # )
            # st.image(recipe['image_url'], use_column_width=True)
            # st.divider()
            click_recipe = st.button(f"**{recipe['recipe_name']}**")
            if click_recipe:
                st.session_state.selected_recipe = recipe


    if st.session_state.selected_recipe:
        rec = st.session_state.selected_recipe

        @st.dialog("Details")
        def show_recipe():
            st.subheader(f"🍴 {rec['recipe_name']}")
            st.markdown(f"**Ingredients:** {rec['ingredients']}")
            st.markdown(f"**Instructions:** {rec['instructions']}")

        show_recipe()