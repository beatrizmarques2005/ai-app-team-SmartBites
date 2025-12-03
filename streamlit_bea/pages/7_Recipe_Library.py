import streamlit as st
from streamlit_bea._common import get_services

st.set_page_config(page_title='Recipes - SmartBites')
services = get_services()
recipe_svc = services['recipe']

st.title('Recipe Library')
ings = st.text_input('Ingredients (comma-separated)')
strict = st.checkbox('Strict', value=True)
if st.button('Search'):
    ingredients = [i.strip() for i in ings.split(',') if i.strip()]
    results = recipe_svc.search_by_ingredients(ingredients, strict=strict)
    st.write(results)
