"""
SmartBites main application entry point.

Purpose:
- Serve as the central router for the SmartBites Streamlit multipage application.
- Handle authentication flow (login/signup) and route authenticated users to feature pages.
- Provide a sidebar navigation menu with icons and a logout button.

UI Flow:
- Initializes session state variables for authentication and navigation.
- If user is not logged in, displays either login or signup page based on `show_signup` flag.
- Once authenticated, renders a sidebar with:
  - SmartBites logo and slogan
  - Navigation menu with icons (Chat, Receipt Analyzer, Planner, Pantry, Shopping List, Profile, About Us)
  - Logout button
  - Version number
- Routes to the selected page based on sidebar menu selection.

Session State Keys:
- `auth`: `AuthService` instance for authentication operations.
- `logged_in`: boolean indicating if user is authenticated.
- `user_id`: authenticated user's unique identifier.
- `email`, `password`: credentials used during login/signup.
- `show_signup`: boolean toggle between login and signup views.
- `current_page`: tracks the currently selected page in the navigation.

Routing:
- Pre-authentication: routes to `login_page()` or `signup_page()`.
- Post-authentication: routes to feature pages based on sidebar selection.

Entry Point:
- This file is the Streamlit application entry point, run via `streamlit run App.py`.
"""
import streamlit as st
from streamlit_option_menu import option_menu
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.authentication import AuthService
from auth_.login import login_page
from auth_.signup import signup_page
from pages_.profile import profile_page
from pages_.chat import chat_page
from pages_.planner import weekly_planner_page
from pages_.pantry import pantry_page
from pages_.receipts import receipts_page
from pages_.shopping_list import shopping_list_page
from pages_.about_us import about_us_page


# Initialize session state defaults
defaults = {
    'auth': AuthService(),
    'logged_in': False,
    'user_id': None,
    'email': '',
    'password': '',
    'show_signup': False,
    'current_page': 'chat'
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

auth = st.session_state.auth

if not st.session_state['logged_in']:
    if st.session_state['show_signup']:
        signup_page()
    else:
        login_page()
    st.stop()


# Sidebar configuration
with st.sidebar:
    st.image("images/SmartBites_Logo.png", use_container_width=True)
    st.markdown("<h1 style='text-align: center; margin-bottom: 0rem;'><em><strong>SmartBites</strong></em></h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-bottom: 0.05rem; font-weight: 400;'>Your ingredients.<br>Your meals.<br>Your way.</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 0.25rem 0; border: 1px solid #e0e0e0;' />", unsafe_allow_html=True)

    # Menu 
    selected = option_menu(
        menu_title= None,  
        options=["Chat", "Receipt Analyzer", "Planner", "Pantry",  "Shopping List", "Profile", "About Us"],
        icons = ["robot", "receipt", "calendar-week", "basket", "list-check", "person", "info-circle"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#ffffffff", "font-size": "20px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"5px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#9eac9996", "color": "white"},
        }
    )
    
    # Style logout button red
    st.markdown(
        """
        <style>
        button[kind="primary"]:has(p) {
            background-color: #c62828 !important;
            color: #fff !important;
            border: 1px solid #b71c1c !important;
        }
        button[kind="primary"]:has(p):hover {
            background-color: #b71c1c !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    

    if st.button("Logout", type="primary", use_container_width=True):
        auth.logout()
        st.session_state.clear()
        st.rerun()
        
# Page routing 
page_routes = {
    "Chat": chat_page,
    "Receipt Analyzer": receipts_page,
    "Planner": weekly_planner_page,
    "Pantry": pantry_page,
    "Shopping List": shopping_list_page,
    "Profile": profile_page,
    "About Us": about_us_page
}

if selected in page_routes:
    page_routes[selected]()