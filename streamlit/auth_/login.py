import streamlit as st
from pathlib import Path
import sys

# Ensure project root is on sys.path so `src` imports work when Streamlit
# runs files from the `streamlit_mariana` package directory.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.authentication import AuthService

def login_page():
    st.title('Login to your Smart Bites Page!')

    # inputs
    st.session_state.email = st.text_input('Email', value =  st.session_state.email, placeholder = 'you@example.com')

    st.session_state.password = st.text_input('Password', value = st.session_state.password, type = 'password', placeholder = '••••••••')

    with st.form('login_form'):
        submitted = st.form_submit_button('Login')

        if submitted:
            try:
                svc = AuthService()
                resp = svc.login(st.session_state.email, st.session_state.password)

                # Support both dict-like and object responses from the client
                user = None
                if hasattr(resp, "user"):
                    user = resp.user
                elif isinstance(resp, dict):
                    user = resp.get("user")

                user_id = None
                if user is not None:
                    # user may be an object with attribute `id` or a dict
                    user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)

                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.auth = svc # Store the auth service in session state
                    st.success("✅ Login successful!")
                    # st.switch_page("app.py")
                    # st.write("User ID:", user_id)
                    st.session_state['logged_in'] = True
                    st.rerun()

                else:
                    st.error("❌ Invalid email or password")

            except Exception:
                st.error("❌ Invalid email or password")

    st.markdown('Don\'t have an account?')
    if st.button('Sign Up', type = 'tertiary'):
        st.session_state['show_signup'] = True
        st.rerun()
