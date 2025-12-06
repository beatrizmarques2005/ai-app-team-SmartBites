import streamlit as st
import sys
import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from dotenv import load_dotenv
from supabase import create_client, Client

# --- Configuration Loading ---
load_dotenv()
SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")

# -----------------------------------------------------
## 🛠️ SUPABASE CLIENT INITIALIZATION
# -----------------------------------------------------
supabase: Client = None 

if not SUPABASE_URL or not SUPABASE_KEY:
    print("FATAL CONFIG ERROR: SUPABASE_URL or SUPABASE_KEY not found in .env file.")
    st.error("Configuration Error: Database credentials missing. Please check your .env file.")
else:
    try:
        # Client creation MUST succeed for the app to function
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error("FATAL ERROR: Could not create Supabase client. Check connection details.")
        print(f"FATAL CLIENT CREATION ERROR: {e}")
        supabase = None

# --- Import Page Components ---
from auth_.login import login_page
from auth_.signup import signup_page
# Assuming you have placeholders for the rest of your pages:
# from pages_.profile import profile_page
# from pages_.chat import chat_page
# from pages_.planner import weekly_planner_page
# from pages_.pantry import pantry_page

# ------------------------------------------------
## 1. SESSION STATE INITIALIZATION
# ------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'auth_mode' not in st.session_state: 
    st.session_state['auth_mode'] = 'login' 
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'profile'


# ------------------------------------------------
## 2. PASSWORD RESET FUNCTIONS (Now accepting 'supabase')
# ------------------------------------------------

def send_reset_email(to_email: str, reset_code: str):
    """Placeholder for actual email sending logic."""
    print(f"DEBUG: Sent code {reset_code} to {to_email}")

def request_password_reset(supabase):
    st.subheader("Request Password Reset")
    email = st.text_input("Enter your email for password reset")

    if st.button("Send Reset Code"):
        if supabase is None: 
            st.error("Database unavailable.")
            return

        try:
            resp = supabase.table("users").select("id, email").eq("email", email).limit(1).execute()
            user_data = resp.data[0] if resp.data else None
            
            if user_data:
                reset_code = f"{secrets.randbelow(1000000):06}"
                supabase.table("users").update({
                    "reset_token": reset_code,
                    "token_expiry": (datetime.now() + timedelta(minutes=30)).isoformat()
                }).eq("id", user_data["id"]).execute()
                send_reset_email(email, reset_code)
            
            st.success("If the email is registered, a password reset code has been sent.")
        except Exception as e:
            st.error("Error processing request. Check console.")
            print(f"Reset Request Error: {e}")
    
    if st.button("Back to Login", key="reset_back_login"):
        st.session_state['auth_mode'] = 'login'
        st.rerun()

def reset_password(supabase):
    st.subheader("Reset Password")
    username = st.text_input("Enter your username")
    code = st.text_input("Enter the 6-digit reset code")
    new_password = st.text_input("Enter your new password", type="password")

    if st.button("Reset Password"):
        if supabase is None: 
            st.error("Database unavailable.")
            return
        
        try:
            resp = supabase.table("users").select("id, reset_token, token_expiry").eq("username", username).limit(1).execute()
            user_data = resp.data[0] if resp.data else None
            
            if not user_data:
                st.error("Invalid username")
                return

            token = user_data.get("reset_token")
            expiry_str = user_data.get("token_expiry")
            expiry = datetime.fromisoformat(expiry_str) if expiry_str else None

            if token != code or not expiry or datetime.now() > expiry:
                st.error("Invalid or expired code")
                return
            
            supabase.table("users").update({
                "password": new_password, # INSECURE: Use hashing in production
                "reset_token": None,
                "token_expiry": None
            }).eq("id", user_data["id"]).execute()
            
            st.success("Password reset successfully! Redirecting to login.")
            st.session_state['auth_mode'] = 'login'
            st.rerun()

        except Exception as e:
            st.error("Error resetting password. Check console.")
            print(f"Password Reset Error: {e}")


# ------------------------------------------------
## 3. UNATHENTICATED ROUTING (Login, Signup, Reset)
# ------------------------------------------------
if not st.session_state['logged_in']:
    
    st.sidebar.title("Smart Bites 🍽️")
    st.sidebar.markdown("---")
    
    auth_mode_map = {
        'Login': 'login', 
        'Sign Up': 'signup', 
        'Request Password Reset': 'request_reset', 
        'Finalize Password Reset': 'reset_password'
    }
    
    selected_mode = st.sidebar.radio(
        "Choose Action", 
        list(auth_mode_map.keys()),
        key='auth_mode_selector'
    )
    st.session_state['auth_mode'] = auth_mode_map[selected_mode]
    
    # --- ROUTING LOGIC (Passing the supabase client) ---
    if st.session_state['auth_mode'] == 'signup':
        signup_page(supabase)