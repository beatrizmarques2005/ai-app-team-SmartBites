import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.db.client import supabase
from src.authentication import AuthService
from src.tools.user_writer import UserWriter

def profile_page():
    st.set_page_config(page_title='User Profile', page_icon='👤', initial_sidebar_state = 'collapsed', layout = 'wide')
    
    st.title('User Profile')

    user_id = st.session_state.get('user_id', None)
    if user_id is None:
        st.error("User not logged in.")
        return 
    
    auth = st.session_state.get('auth', None)
    if auth is None:
        st.error("Authentication service not available.")
        return


    user_writer = UserWriter(auth)
    
    try:
        response = supabase.table('users').select('*').eq('user_id', user_id).execute()

        user = response.data[0] if response.data else None
        if not user:
            st.error("User not found.")
            return
        
    except Exception as e:
        st.error("Error fetching user data.")
        st.write(str(e))
        return 


    st.subheader(f"Hello, {user.get('full_name', 'User')}!")

    st.markdown(f"**Full Name:** {user.get('full_name', '')}")
    st.markdown(f"**Birth Date:** {user.get('birth_date', '')}")
    st.markdown(f"**Gender:** {user.get('gender', '')}")
    st.markdown(f"**Default Household Number:** {user.get('household_number', '')}")
    st.markdown(f"**Dietary Restrictions:** {', '.join(user.get('restrictions', [])) if user.get('restrictions') else ''}")
    st.markdown(f"**Diet Type:** {', '.join(user.get('diet_type', [])) if user.get('diet_type') else ''}")
    st.markdown(f"**Cuisine Type Preferences:** {', '.join(user.get('cuisine_type', [])) if user.get('cuisine_type') else ''}")

    
    # EDIT PROFILE SECTION
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False

    if not st.session_state.edit_mode:
        if st.button("Edit Profile"):
            st.session_state.edit_mode = True
            st.rerun()

    else:
        with st.form(key='edit_profile_form'):
            full_name = st.text_input("Full Name", value=user.get('full_name', ''))
            birth_date = st.date_input("Birth Date", value=user.get('birth_date', None))
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"], index=["", "Male", "Female", "Other"].index(user.get('gender', '') or ""))
            household_number = st.number_input("Default Household Number", value=int(user.get('household_number', 1)) if user.get('household_number') else 1, min_value=1)
            
            diet_options = ["None", "Vegetarian", "Vegan", "Pescatarian", "Keto", "Gluten-Free", "Dairy-Free"]
            cuisine_options = ["None", "Italian", "Mexican", "Indian", "Chinese", "Mediterranean",
                        "American", "Portuguese"]
            restrictions_options = ["None", "Nut Allergy", "Dairy Allergy", "Gluten Allergy", "Shellfish Allergy", "Lactose Intolerance"]

            restrictions = st.multiselect(
                "Dietary Restrictions (allergies, intolerances, dislikes)",
                restrictions_options,
                default=(user.get('restrictions') or []),
                accept_new_options=True,
            )

            diet_type = st.multiselect(
                "Diet Type",
                diet_options,
                default=(user.get('diet_type') or []),
                accept_new_options=True,
            )

            cuisine_type = st.multiselect(
                "Preferred cuisines",
                cuisine_options,
                default=(user.get('cuisine_type') or []),
                accept_new_options=True,
            )
            
            col1, col2, col3 = st.columns([2, 5, 1])
            with col1:
                submitted = st.form_submit_button("Save Changes")
            with col3:
                cancel = st.form_submit_button("Cancel")
        
        if submitted:
            try:
                user_writer.update_user_profile(
                    full_name=full_name,
                    birth_date=str(birth_date) if birth_date else None,
                    gender=gender,
                    household_number=household_number,
                    restrictions=restrictions,
                    diet_type=diet_type,
                    cuisine_type=cuisine_type
                )
                st.success("Profile updated successfully!")
                st.session_state.edit_mode = False
                st.rerun()
            except Exception as e:
                st.error(f"Error updating profile: {str(e)}")
        
        if cancel:
            st.session_state.edit_mode = False
            st.rerun()
