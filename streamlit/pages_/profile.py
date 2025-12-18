import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.db.client import supabase
from src.authentication import AuthService

def profile_page():
    st.set_page_config(page_title='User Profile', page_icon='👤')
    
    st.title('User Profile')

    auth = AuthService()
    user_id = st.session_state.get('user_id', None)
    if user_id is None:
        st.error("User not logged in.")
        return 
    
    try:
        response = supabase.table('users').select('*').eq('user_id', user_id).execute()

        user = response.data[0]
        st.subheader(f"Hello, {user.get('full_name', 'User')}!")

        st.markdown(f"**Full Name:** {user.get('full_name', '')}")
        st.markdown(f"**Birth Date:** {user.get('birth_date', '')}")
        st.markdown(f"**Gender:** {user.get('gender', '')}")
        st.markdown(f"**Default Household Number:** {user.get('household_number', '')}")
        st.markdown(f"**Dietary Restrictions:** {', '.join(user.get('restrictions', [])) if user.get('restrictions') else ''}")
        st.markdown(f"**Diet Type:** {', '.join(user.get('diet_type', [])) if user.get('diet_type') else ''}")
        st.markdown(f"**Favourite Recipes:** {', '.join(user.get('favourite_recipes', [])) if user.get('favourite_recipes') else ''}")
        st.markdown(f"**Cuisine Type Preferences:** {', '.join(user.get('cuisine_type', [])) if user.get('cuisine_type') else ''}")

    except Exception as e:
        st.error("Error fetching user info.")
        st.write(str(e))