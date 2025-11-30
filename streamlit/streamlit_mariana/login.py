import streamlit as st
from supabase_client import supabase
from pages import profile

st.set_page_config(
    page_title="Login",
    initial_sidebar_state="collapsed",
    layout="centered"
)

st.title("Login to your SmartBites Page!")

# ---------------- SESSION INIT ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

# ---------------- INPUTS ----------------
email = st.text_input("Email")
password = st.text_input("Password", type="password")

# ---------------- LOGIN ----------------
if st.button("Login"):
    try:
        auth = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        st.session_state.logged_in = True
        st.session_state.user_id = auth.user.id
        st.success("Logged in successfully!")

        profile.profile_page()

    except Exception as e:
        st.error("Invalid credentials")
        st.error(e)

# ---------------- SIGN UP ----------------
st.markdown("Don't have an account?")

if st.button("Sign Up", type="tertiary"):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        st.success("Account created successfully! You can now log in.")

    except Exception as e:
        st.error("Error creating account")
        st.error(e)
