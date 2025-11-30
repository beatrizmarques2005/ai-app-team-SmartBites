import streamlit as st
from supabase_client import supabase

st.set_page_config(
    page_title="SmartBites | Login",
    layout="centered"
)

st.title("🍽️ SmartBites")
st.subheader("Your personal food assistant")

# ---------- SESSION STATE ----------
if "mode" not in st.session_state:
    st.session_state.mode = "login"  # or "signup"

if "email" not in st.session_state:
    st.session_state.email = ""

if "password" not in st.session_state:
    st.session_state.password = ""

if "user_id" not in st.session_state:
    st.session_state.user_id = None


# ---------- MODE TOGGLE ----------
col1, col2 = st.columns(2)

with col1:
    if st.button("🔐 Login"):
        st.session_state.mode = "login"
        st.session_state.email = ""
        st.session_state.password = ""

with col2:
    if st.button("📝 Sign Up"):
        st.session_state.mode = "signup"
        st.session_state.email = ""
        st.session_state.password = ""


st.markdown("---")

# ---------- INPUTS ----------
st.session_state.email = st.text_input(
    "Email",
    value=st.session_state.email,
    placeholder="you@example.com"
)

st.session_state.password = st.text_input(
    "Password",
    value=st.session_state.password,
    type="password",
    placeholder="••••••••"
)


# ---------- LOGIN LOGIC ----------
if st.session_state.mode == "login":
    st.button("✅ Login", key="login_btn")

    if st.session_state.get("login_btn"):
        with st.spinner("Logging in..."):
            try:
                auth = supabase.auth.sign_in_with_password({
                    "email": st.session_state.email,
                    "password": st.session_state.password
                })

                st.session_state.user_id = auth.user.id
                st.success("✅ Login successful!")
                st.switch_page("app.py")

                st.write("User ID:", auth.user.id)

            except Exception:
                st.error("❌ Invalid email or password")


# ---------- SIGN UP LOGIC ----------
if st.session_state.mode == "signup":
    st.button("🚀 Create Account", key="signup_btn")

    if st.session_state.get("signup_btn"):
        with st.spinner("Creating account..."):
            try:
                supabase.auth.sign_up({
                    "email": st.session_state.email,
                    "password": st.session_state.password
                })

                st.success("✅ Account created! You can now log in.")

                # Switch automatically to login
                st.session_state.mode = "login"
                st.session_state.password = ""

            except Exception as e:
                st.error("❌ Error creating account")
                st.error(e)
