"""
Profile page for the SmartBites Streamlit app.

Purpose:
- Display and edit user profile information (name, birth date, gender, household, dietary preferences).
- Persist profile changes to the Supabase `users` table via `UserWriter`.

UI Flow:
- Configures the page (title, icon, wide layout, collapsed sidebar).
- Auth gate: requires `user_id` and `auth` in session; otherwise shows error and stops.
- Queries the `users` table to load current profile data.
- Displays profile info (full name, birth date, gender, household, restrictions, diet type, cuisines).
- "Edit Profile" button toggles edit mode, showing a form with prefilled values, where user can modify their information and updates the database.

Session State Keys:
- `user_id`: authenticated user identifier required for data scoping.
- `auth`: `AuthService` instance required for `UserWriter`.
- `edit_mode`: bool toggling between view and edit modes.

Database Schema:
- Reads and writes to `users` table with fields: `user_id`, `full_name`, `birth_date`, `gender`, `household_number`, `restrictions`, `diet_type`, `cuisine_type`.

Entry Point:
- `profile_page()`: renders profile UI and handles form submission via `UserWriter`.
"""
import streamlit as st
from langfuse import observe
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.db.client import supabase
from src.authentication import AuthService
from src.tools.user_writer import UserWriter

if "auth" not in st.session_state:
    st.session_state.auth = AuthService()

@observe
def profile_page():
    st.set_page_config(
        page_title='User Profile',
        page_icon='https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/person-circle.svg',
        initial_sidebar_state='collapsed',
        layout='wide'
    )
    
    st.title('User Profile')

    auth = st.session_state.auth
    user_id = st.session_state.get('user_id', None) or auth.get_user_id()
    
    if user_id is None:
        st.error("User not logged in.")
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

    # Display user information
    full_name = user.get('full_name', 'User')
    first_name = full_name.split()[0] if full_name and full_name.strip() else 'User'
    st.subheader(f"Hello, {first_name}!")

    st.markdown(f"**Full Name:** {user.get('full_name', '')}")
    st.markdown(f"**Birth Date:** {user.get('birth_date', '')}")
    st.markdown(f"**Gender:** {user.get('gender', '')}")
    st.markdown(f"**Default Household Number:** {user.get('household_number', '')}")
    st.markdown(f"**Dietary Restrictions:** {', '.join(user.get('restrictions', [])) if user.get('restrictions') else ''}")
    st.markdown(f"**Diet Type:** {', '.join(user.get('diet_type', [])) if user.get('diet_type') else ''}")
    st.markdown(f"**Cuisine Type Preferences:** {', '.join(user.get('cuisine_type', [])) if user.get('cuisine_type') else ''}")

    
    # Edit profile section
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
            
            gender_options = ["Prefer not to say", "Male", "Female", "Other"]
            current_gender = user.get('gender', 'Prefer not to say')
            gender_index = gender_options.index(current_gender) if current_gender in gender_options else 0
            gender = st.selectbox("Gender", gender_options, index=gender_index)
            
            household_number = st.number_input("Default Household Number", value=int(user.get('household_number', 1)) if user.get('household_number') else 1, min_value=1)
            
            diet_options = ["None", "Vegetarian", "Vegan", "Pescatarian", "Keto", "Gluten-Free", "Dairy-Free"]
            cuisine_options = ["None", "Italian", "Mexican", "Indian", "Chinese", "Mediterranean",
                        "American", "Portuguese"]
            restrictions_options = ["None", "Nut Allergy", "Dairy Allergy", "Gluten Allergy", "Shellfish Allergy", "Lactose Intolerance"]

            user_restrictions = user.get('restrictions') or []
            user_diet_type = user.get('diet_type') or []
            user_cuisine_type = user.get('cuisine_type') or []
            
            all_restrictions = restrictions_options + [r for r in user_restrictions if r not in restrictions_options]
            all_diet_options = diet_options + [d for d in user_diet_type if d not in diet_options]
            all_cuisine_options = cuisine_options + [c for c in user_cuisine_type if c not in cuisine_options]

            restrictions = st.multiselect(
                "Dietary Restrictions (allergies, intolerances, dislikes)",
                all_restrictions,
                default=user_restrictions,
                accept_new_options=True,
            )

            diet_type = st.multiselect(
                "Diet Type",
                all_diet_options,
                default=user_diet_type,
                accept_new_options=True,
            )

            cuisine_type = st.multiselect(
                "Preferred cuisines",
                all_cuisine_options,
                default=user_cuisine_type,
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
