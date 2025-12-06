# C:\Users\wwwnj\...\streamlit_copy\auth_\login.py

import streamlit as st

def login_page(supabase_client):
    st.title('Login to your Smart Bites Page!')

    with st.form('login_form'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        submitted = st.form_submit_button('Login')

        if submitted:
            if supabase_client is None:
                st.error("Configuration Error: Database connection is not available.")
                return

            try:
                # 1. Query the database for the user by username
                resp = supabase_client.table("users").select("id, username, password").eq("username", username).limit(1).execute()
                
                if resp.error:
                    st.error("Database query failed. Check console for RLS or config errors.")
                    print(f"Supabase Query Error: {resp.error}")
                    return
                user_data = resp.data[0] if resp.data else None
            
            except Exception as e:
                st.error("A critical database error occurred. Check your console output for details.")
                print(f"CRITICAL Supabase Login Error: {e}")
                return

            # 2. Check if user exists and if the password matches
            if user_data:
                db_password = user_data.get("password")
                
                if db_password == password:
                    # SUCCESS
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['user_id'] = user_data.get("id") 
                    st.success('Logged in successfully')
                    st.rerun()
                else:
                    st.error('Invalid username or password (Password Mismatch)')
            else:
                st.error('Invalid username or password (User Not Found)')