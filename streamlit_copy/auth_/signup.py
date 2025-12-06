# C:\Users\wwwnj\...\streamlit_copy\auth_\signup.py

import streamlit as st

def signup_page(supabase_client): 
    st.title('Create your Smart Bites Account')
    
    with st.form('signup_form'):
        username = st.text_input('Username')
        email = st.text_input('Email')
        password = st.text_input('Password', type='password')
        confirm_password = st.text_input('Confirm Password', type='password')
        submitted = st.form_submit_button('Sign Up')

        if submitted:
            if supabase_client is None:
                st.error("Configuration Error: Database connection is not available.")
                return

            # 1. Basic Validation
            if not all([username, email, password, confirm_password]):
                st.error("All fields are required.")
                return
            if password != confirm_password:
                st.error("Passwords do not match.")
                return
            
            # 2. Supabase Check for Existing User
            try:
                # Uses .or_ to check if EITHER username or email is taken
                existing_user_resp = supabase_client.table("users") \
                    .select("id") \
                    .or_(f"username.eq.{username},email.eq.{email}") \
                    .execute()
                    
                if existing_user_resp.data:
                    st.error("A user with this username or email already exists.")
                    return
            except Exception as e:
                st.error("Database error during pre-check. See console.")
                print(f"Supabase Signup Pre-Check Error: {e}")
                return

            # 3. ACTUAL SUPABASE INSERTION
            try:
                insert_resp = supabase_client.table("users").insert({
                    "username": username,
                    "email": email,
                    "password": password
                }).execute()

                if insert_resp.error:
                    st.error(f"Failed to create user account: {insert_resp.error.message}")
                    print(f"Supabase Insert Error: {insert_resp.error.message}")
                    return

                # 4. Success and Redirection
                st.success("Account created successfully! Please proceed to Login.")
                st.session_state['auth_mode'] = 'login' 
                st.rerun()

            except Exception as e:
                st.error("An unexpected error occurred during signup.")
                print(f"Generic Signup Error: {e}")