import streamlit as st
# from pages import profile
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)
    
from src.db.client import supabase


def login_page():
    st.title('Login to your Smart Bites Page!')

    

    with st.form('login_form'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        submitted = st.form_submit_button('Login')

        if submitted:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success('Logged in successfully')
                st.rerun()
            # resp = supabase.table('users').select('*').eq('username', username).limit(1).execute()
            # user_rows = getattr(resp, "data", []) or []

            # if not user_rows:
            #     st.error('Not registered')
            # else:
            #     user = user_rows[0]
            #     stored_pw = user.get("password")

            #     if stored_pw == password:
            #         st.session_state['logged_in'] = True
            #         st.session_state['username'] = username
            #         st.success('Logged in successfully')
            #         st.rerun()
            #     else:
            #         st.error('Invalid credentials')

    st.markdown('Don\'t have an account?')
    if st.button('Sign Up', type = 'tertiary'):
        st.session_state['show_signup'] = True
        st.rerun()



