import streamlit as st
from supabase_client import supabase

def profile_page():
    if not st.session_state.get("logged_in"):
        st.error("You must be logged in")
        return

    user_id = st.session_state["user_id"]

    st.title("My Profile")
    st.write("My user id:", user_id)

    # Exemplo: buscar dados do utilizador
    data = supabase.table("pantry_items").select("*").execute()

    st.write(data.data)
