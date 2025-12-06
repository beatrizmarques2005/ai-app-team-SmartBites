import streamlit as st
from auth_.login import login_page
from auth_.signup import signup_page
from pages_.profile import profile_page
from pages_.chat import chat_page
from pages_.planner import weekly_planner_page
from pages_.pantry import pantry_page
from pages_.recipes import recipes_page
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.services.auth_service import AuthService
auth = AuthService()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'username' not in st.session_state:
    st.session_state['username'] = ''

if 'email' not in st.session_state:
    st.session_state['email'] = ''

if 'password' not in st.session_state:
    st.session_state['password'] = ''

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

if 'show_signup' not in st.session_state:
    st.session_state['show_signup'] = False

if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'chat'



if not st.session_state['logged_in']:
    if st.session_state['show_signup']:
        signup_page()
    else:
        login_page()
    st.stop()



if st.sidebar.button('Profile', type = 'tertiary'):
    st.session_state['current_page'] = 'profile'
if st.sidebar.button('Chat', type = 'tertiary'):
    st.session_state['current_page'] = 'chat'
if st.sidebar.button('Planner', type = 'tertiary'):
    st.session_state['current_page'] = 'planner'
if st.sidebar.button('Pantry', type = 'tertiary'):
    st.session_state['current_page'] = 'pantry'
if st.sidebar.button('Recipes', type = 'tertiary'):
    st.session_state['current_page'] = 'recipes'



st.sidebar.empty().write("")  # Add some space

if st.sidebar.button('Logout'):
        auth.logout()
        st.session_state.clear()
        st.rerun()

if st.session_state['current_page'] == 'profile':
    profile_page()
elif st.session_state['current_page'] == 'chat':
    chat_page()
elif st.session_state['current_page'] == 'planner':
    weekly_planner_page()
elif st.session_state['current_page'] == 'pantry':
    pantry_page()
elif st.session_state['current_page'] == 'recipes':
    recipes_page()

