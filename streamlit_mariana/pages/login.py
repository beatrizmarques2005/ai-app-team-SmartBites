import streamlit as st
from pathlib import Path
import sys

# Ensure project root is on sys.path so `src` imports work when Streamlit
# runs files from the `streamlit_mariana` package directory.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.services.auth_service import AuthService

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
                    st.success("✅ Login successful!")
                    st.switch_page("app.py")
                    st.write("User ID:", user_id)
                else:
                    st.error("❌ Invalid email or password")

            except Exception:
                st.error("❌ Invalid email or password")


# ---------- SIGN UP LOGIC ----------
if st.session_state.mode == "signup":
    st.button("🚀 Create Account", key="signup_btn")

    if st.session_state.get("signup_btn"):
        with st.spinner("Creating account..."):
            try:
                svc = AuthService()
                svc.signup(st.session_state.email, st.session_state.password)

                st.success("✅ Account created! You can now log in.")

                # Switch automatically to login
                st.session_state.mode = "login"
                st.session_state.password = ""

            except Exception as e:
                st.error("❌ Error creating account")
                st.error(e)
