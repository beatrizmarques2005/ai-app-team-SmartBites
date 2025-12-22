import streamlit as st
from streamlit_option_menu import option_menu
from auth_.login import login_page
from auth_.signup import signup_page
from pages_.profile import profile_page
from pages_.chat import chat_page
from pages_.planner import weekly_planner_page
from pages_.pantry import pantry_page
from pages_.receipts import receipts_page
from pages_.shopping_list import shopping_list_page
from pages_.about_us import about_us_page


import sys
from pathlib import Path


from src.authentication import AuthService

if "auth" not in st.session_state:
    st.session_state.auth = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False



ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.authentication import AuthService
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


with st.sidebar:
    st.image("images\SmartBites_logo.png", use_container_width=True)
    st.markdown("<h1 style='text-align: center; margin-bottom: 0rem;'><em><strong>SmartBites</strong></em></h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-bottom: 0.05rem; font-weight: 400;'>Your ingredients.<br>Your meals.<br>Your way.</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 0.25rem 0; border: 1px solid #e0e0e0;' />", unsafe_allow_html=True)
    selected = option_menu(
        menu_title= None, 
        # menu_icon= None, 
        options=[ "Chat", "Receipt Analyzer", "Planner", "Pantry",  "Shopping List", "Profile", "About Us"],
        icons = ["robot", "receipt", "calendar-week", "basket", "list-check", "person", "info-circle"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#555", "font-size": "20px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"5px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#0f67166e", "color": "black"}, # The "pill" effect
        }
    )
    
    # Dynamic spacer that fills remaining space
    st.markdown(
        """
        <style>
        /* Make sidebar scrollable and add spacer */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding-bottom: 80px;
        }
        
        /* Style logout button red */
        button[kind="primary"]:has(p) {
            background-color: #c62828 !important;
            color: #fff !important;
            border: 1px solid #b71c1c !important;
        }
        button[kind="primary"]:has(p):hover {
            background-color: #b71c1c !important;
        }
        </style>
        <div style="flex-grow: 1;"></div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Logout", type="primary"):
        auth.logout()
        st.session_state.clear()
        st.rerun()
        
    st.markdown("<span style='font-size: 0.9rem;'>version 1.0</span>", unsafe_allow_html=True)

page_map = {
    "Profile": "profile",
    "Chat": "chat",
    "Receipt Analyzer": "receipts",
    "Planner": "planner",
    "Pantry": "pantry",
    "Shopping List": "shopping_list", 
    "About Us": "about_us"
}




st.session_state['current_page'] = page_map[selected]

if st.session_state['current_page'] == 'profile':
    profile_page()
elif st.session_state['current_page'] == 'chat':
    chat_page()
elif st.session_state['current_page'] == 'planner':
    weekly_planner_page()
elif st.session_state['current_page'] == 'pantry':
    pantry_page()
elif st.session_state['current_page'] == 'receipts':
    receipts_page()
elif st.session_state['current_page'] == 'shopping_list':
    shopping_list_page()
elif st.session_state['current_page'] == 'about_us':
    about_us_page()
    
    