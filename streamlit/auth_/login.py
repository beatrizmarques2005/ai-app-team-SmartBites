"""
Login page for the SmartBites Streamlit app.

Purpose:
- Render email/password inputs inside a Streamlit form.
- Authenticate the user via `AuthService.login()`.
- Persist relevant authentication details in `st.session_state`.
- Provide a route to the signup flow when the user has no account.

UI Flow:
- Displays a title and two inputs: `email` and `password`.
- The `Login` form button submits credentials and calls `AuthService.login()`.
- On success, it extracts the authenticated `user.id`, stores it in session, sets
    `auth` and `logged_in`, shows a success message, and triggers `st.rerun()`.
- On failure, it shows an error message without crashing.
- A secondary "Don't have an account? Sign up" button sets `show_signup=True`
    and `st.rerun()` so the router moves to the signup page.

Session State Keys:
- `email`, `password`: input values are persisted across reruns.
- `user_id`: Supabase user identifier set after successful login.
- `auth`: the `AuthService` instance for downstream use.
- `logged_in`: boolean gate for authenticated routes.
- `show_signup`: flag used by the app's router to display the signup screen.

Entry Point:
- `login_page()`: renders the login UI and handles submission logic.
"""

import streamlit as st
from langfuse import observe
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.authentication import AuthService

@observe
def login_page():
    st.set_page_config(
        page_title="SmartBites | Login",
        page_icon="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/person-circle.svg",
        layout="centered",
        initial_sidebar_state='collapsed'
    )
    st.title('Login to your *SmartBites* Account!')

    st.session_state.email = st.text_input('Email', value =  st.session_state.email, placeholder = 'you@example.com')

    st.session_state.password = st.text_input('Password', value = st.session_state.password, type = 'password', placeholder = '••••••••')

    with st.form('login_form'):
        submitted = st.form_submit_button('Login')

        if submitted:
            try:
                auth = AuthService()
                resp = auth.login(st.session_state.email, st.session_state.password)

                user = None
                if hasattr(resp, "user"):
                    user = resp.user
                elif isinstance(resp, dict):
                    user = resp.get("user")

                user_id = None
                if user is not None:
                    user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)

                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.auth = auth 
                    st.success("Login successful!")
                    st.session_state['logged_in'] = True
                    st.rerun()

                else:
                    st.error("Invalid email or password")

            except Exception:
                st.error("Invalid email or password")

    st.markdown("---")

    if st.button("Don't have an account? Sign up"):
        st.session_state["show_signup"] = True
        st.rerun()