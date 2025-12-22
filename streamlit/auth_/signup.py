import streamlit as st
from pathlib import Path
import sys
import datetime
from datetime import date

# Ensure project root is on sys.path so `src` imports work when Streamlit
# runs files from the `streamlit_mariana` package directory.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.authentication import AuthService
from src.db.client import supabase

def signup_page():
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

    
    # STEP 0 – Create account (email + password)
    if step == 0:
        st.header("Step 1 — Create your account")

        with st.form("step_0"):
            # inputs
            st.session_state.email = st.text_input('Email', value =  st.session_state.email, placeholder = 'you@example.com')

            st.session_state.password = st.text_input('Password', value = st.session_state.password, type = 'password', placeholder = '••••••••')
            create_button = st.form_submit_button("Create Account")

            if create_button:
                try:
                    resp = svc.signup(st.session_state.email, st.session_state.password)

                    error = getattr(resp, "error", None) or resp.get("error") if isinstance(resp, dict) else None
                    if error:
                        st.error(f"Signup failed: {error['message'] if isinstance(error, dict) else error}")
                    else:
                        user = getattr(resp, "user", None) or resp.get("user")
                        if user:
                            st.session_state.user_id = getattr(user, "id", None) or user.get("id")
                            st.success("Account created successfully!")
                            st.session_state.signup_step = 1
                            st.rerun()
                        else:
                            st.error("Signup failed: no user returned from Supabase")

                except Exception as e:
                    st.error("❌ Error creating account")
                    st.error(e)


    # STEP 1 – Personal info
    elif step == 1:
        st.header("Step 2 — Personal information")
        with st.form("step_1"):
            st.session_state.full_name = st.text_input("Full name")
            st.session_state.birth_date = st.date_input("Birth date", value= datetime.date(2000, 1, 1),  min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today() )
            st.session_state.gender = st.selectbox("Gender", options = ["Prefer not to say", "Female", "Male", "Other"], index = 0)
            st.session_state.household_number = st.number_input("Number of people in household", min_value=1, value=1)
            st.session_state.nationality = st.text_input("Nationality / Geographic area", placeholder="e.g. Portuguese, European, Latin American")
            next_clicked = st.form_submit_button("Next")

            if next_clicked:
                st.session_state.signup_step = 2
                st.rerun()

    # STEP 3 – Preferences + INSERT into Supabase
    elif step == 2:
        st.header("Step 3 — Preferences")

        diet_options = ["None", "Vegetarian", "Vegan", "Pescatarian", "Keto", "Gluten-Free", "Dairy-Free"]
        cuisine_options = ["None", "Italian", "Mexican", "Indian", "Chinese", "Mediterranean",
                        "American", "Portuguese"]
        restrictions_options = ["None", "Nut Allergy", "Dairy Allergy", "Gluten Allergy", "Shellfish Allergy", "Lactose Intolerance"]

        with st.form("step_3"):
            st.session_state.dietary = st.multiselect("Dietary preferences - choose one or more options, or add your own", diet_options, accept_new_options = True)
            st.session_state.restrictions = st.multiselect("Restrictions (allergies, intolerances, dislikes) - choose one or more options, or add your own", restrictions_options, accept_new_options = True)
            st.session_state.cuisines = st.multiselect("Preferred cuisines - choose one or more options, or add your own", cuisine_options, accept_new_options = True)
        
            create_clicked = st.form_submit_button("Create Account")

            if create_clicked:
                # --- INSERT MORE DATA INTO SUPABASE `users` TABLE ---
                user_data['user_id'] = st.session_state.user_id
                user_data['full_name'] = st.session_state.full_name
                user_data['birth_date'] = st.session_state.birth_date.isoformat()
                user_data['gender'] = st.session_state.gender
                user_data['household_number'] = st.session_state.household_number
                user_data['nationality'] = st.session_state.nationality
                user_data['diet_type'] = st.session_state.dietary
                user_data['restrictions'] = st.session_state.restrictions
                user_data['cuisine_type'] = st.session_state.cuisines
                try:
                    

                    supabase.table("users").insert(user_data).execute()

                     # --- SUCCESS ---
                    st.success("🎉 Account created successfully!")

                    # Log the user in after successful signup
                    try:
                        login_resp = svc.login(st.session_state.email, st.session_state.password)
                        st.session_state.auth = svc  # Store the auth service in session state
                        st.session_state['logged_in'] = True
                        st.rerun()
                    except Exception as login_error:
                        st.error(f"Account created but login failed: {login_error}")
                        st.error("Please go back to login page and sign in.")
                        return
                except Exception as e:
                    st.error(f"Database insert failed: {e}")
                    return

               

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("Back", type="tertiary") and step > 0:
            st.session_state.signup_step = step - 1
            st.rerun()

    with col3:
        if st.button("Cancel / Clear", type="tertiary"):
            st.session_state.signup_step = 0
            st.session_state.signup_data = {}
            st.rerun()


    st.markdown("---")

    if st.button("Already have an account? Log in"):
        st.session_state["show_signup"] = False
        st.rerun()