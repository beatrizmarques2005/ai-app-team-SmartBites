"""
Signup page for the SmartBites Streamlit app.

Purpose:
- Render a 3-step wizard to collect user credentials and profile details.
- Create a Supabase auth user via `AuthService.signup()`.
- Persist user profile data in the `users` table.
- Log the user in automatically on successful account creation.

UI Flow:
- Step 0: Email and password form; calls `AuthService.signup()`, extracts `user.id`, advances to step 1.
- Step 1: Personal information (name, birth date, gender, household, nationality); advances to step 2.
- Step 2: Preferences (diet type, ingredient restrictions, preferred cuisines); inserts consolidated profile to `users` table,
    logs in via `AuthService.login()`, sets `auth` and `logged_in`, and triggers `st.rerun()`.
- Progress bar displays current step (0..2) out of 3.
- Back button navigates to previous step; Cancel/Clear resets wizard state.

Session State Keys:
- Input fields: `email`, `password`, `full_name`, `birth_date`, `gender`, `household_number`,
    `nationality`, `dietary`, `restrictions`, `cuisines`.
- Flow control: `signup_step` (0, 1, or 2 internally; displayed as Steps 1-3 to user).
- Auth: `auth` (AuthService instance), `logged_in` (boolean flag for authenticated state).
- Routing: `show_signup` (flag used by app router to toggle between signup and login views).

Database Schema:
- Inserts into `users` table with fields: user_id, full_name, birth_date, gender, household_number,
    nationality, diet_type, restrictions, cuisine_type.

Entry Point:
- `signup_page()`: renders the wizard UI and handles form submission logic across all steps.
"""
import streamlit as st
from langfuse import observe
from pathlib import Path
import sys
import datetime
from datetime import date
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.authentication import AuthService
from src.db.client import supabase

@observe
def signup_page():
    st.set_page_config(
        page_title="SmartBites | Sign Up",
        page_icon="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/person-circle.svg",
        layout="centered",
        initial_sidebar_state='collapsed'
    )

    st.title('Create your *SmartBites* Account!')

    user_data = {
        'user_id': None,
        'full_name': '',
        'birth_date': date(2000, 1, 1),
        'gender': '',
        'nationality': '',
        'household_number': '',
        'restrictions': [],
        'diet_type': [],
        'cuisine_type': []        
        }
    
    for key, default in user_data.items():
        if key not in st.session_state:
            st.session_state[key] = default


    if 'signup_step' not in st.session_state:
        st.session_state.signup_step = 0

    step = st.session_state.signup_step
    total_steps = 3
    st.progress(int((step / total_steps) * 100))

    svc = AuthService()

    # STEP 0 – Collect credentials (no signup yet)
    if step == 0:
        st.header("Step 1 — Your credentials")

        with st.form("step_0"):
            st.session_state.email = st.text_input('Email', value =  st.session_state.email, placeholder = 'you@example.com')
            st.session_state.password = st.text_input('Password', value = st.session_state.password, type = 'password', placeholder = '••••••••')

            next_button = st.form_submit_button("Next")
            if next_button:
                if st.session_state.email and st.session_state.password:
                    st.session_state.signup_step = 1
                    st.rerun()
                else:
                    st.error("Please fill in both email and password")

    # STEP 1 – Personal information
    elif step == 1:
        st.header("Step 2 — Personal information")
        with st.form("step_1"):
            st.session_state.full_name = st.text_input("Full name", value=st.session_state.full_name)
            st.session_state.birth_date = st.date_input("Birth date", value=st.session_state.birth_date, min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
            
            gender_options = ["Prefer not to say", "Female", "Male", "Other"]
            gender_index = gender_options.index(st.session_state.gender) if st.session_state.gender in gender_options else 0
            st.session_state.gender = st.selectbox("Gender", options=gender_options, index=gender_index)
            
            st.session_state.household_number = st.number_input("Number of people in household", min_value=1, value=int(st.session_state.household_number) if st.session_state.household_number else 1)
            st.session_state.nationality = st.text_input("Nationality / Geographic area", value=st.session_state.nationality, placeholder="e.g. Portuguese, European, Latin American")

            next_clicked = st.form_submit_button("Next")
            if next_clicked:
                st.session_state.signup_step = 2
                st.rerun()

    # STEP 3 – Preferences + insert into Supabase
    elif step == 2:
        st.header("Step 3 — Preferences")

        diet_options = ["None", "Vegetarian", "Vegan", "Pescatarian", "Keto", "Gluten-Free", "Dairy-Free"]
        cuisine_options = ["None", "Italian", "Mexican", "Indian", "Chinese", "Mediterranean",
                        "American", "Portuguese"]
        restrictions_options = ["None", "Nut Allergy", "Dairy Allergy", "Gluten Allergy", "Shellfish Allergy", "Lactose Intolerance"]

        with st.form("step_3"):
            st.session_state.dietary = st.multiselect(
                "Dietary preferences - choose one or more options, or add your own", 
                diet_options, 
                default=st.session_state.dietary if st.session_state.dietary else [],
                accept_new_options=True
            )
            st.session_state.restrictions = st.multiselect(
                "Restrictions (allergies, intolerances, dislikes) - choose one or more options, or add your own", 
                restrictions_options,
                default=st.session_state.restrictions if st.session_state.restrictions else [],
                accept_new_options=True
            )
            st.session_state.cuisines = st.multiselect(
                "Preferred cuisines - choose one or more options, or add your own", 
                cuisine_options,
                default=st.session_state.cuisines if st.session_state.cuisines else [],
                accept_new_options=True
            )
        
            create_clicked = st.form_submit_button("Create Account")
            if create_clicked:
                try:
                    # Step 1: Create auth account
                    resp = svc.signup(st.session_state.email, st.session_state.password)
                    
                    error = getattr(resp, "error", None) or resp.get("error") if isinstance(resp, dict) else None
                    if error:
                        st.error(f"Signup failed: {error['message'] if isinstance(error, dict) else error}")
                        return
                    
                    user = getattr(resp, "user", None) or resp.get("user")
                    if not user:
                        st.error("Signup failed: no user returned from Supabase")
                        return
                    
                    user_id = getattr(user, "id", None) or user.get("id")
                    
                    # Step 2: Insert user profile into database
                    user_data['user_id'] = user_id
                    user_data['full_name'] = st.session_state.full_name
                    user_data['birth_date'] = st.session_state.birth_date.isoformat()
                    user_data['gender'] = st.session_state.gender
                    user_data['household_number'] = st.session_state.household_number
                    user_data['nationality'] = st.session_state.nationality.lower()
                    user_data['diet_type'] = st.session_state.dietary
                    user_data['restrictions'] = st.session_state.restrictions
                    user_data['cuisine_type'] = st.session_state.cuisines
                    
                    supabase.table("users").insert(user_data).execute()

                    # Step 3: Log the user in
                    login_resp = svc.login(st.session_state.email, st.session_state.password)
                    st.session_state.auth = svc  
                    st.session_state['logged_in'] = True
                    st.session_state.user_id = user_id
                    st.success("Account created successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Account creation failed: {e}")
                    return

        
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        # Go to previous step or login page
        if st.button("Back", type="tertiary"): 
            if step > 0:
                st.session_state.signup_step = step - 1
                st.rerun()

            elif step == 0:
                st.session_state["show_signup"] = False
                st.rerun()

    with col3:
        # Cancel / Clear all inputs and return to step 0
        if st.button("Cancel / Clear", type="tertiary"):
            st.session_state.signup_step = 0
            st.session_state.signup_data = {}
            st.rerun()
