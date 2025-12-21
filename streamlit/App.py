import streamlit as st
from streamlit_option_menu import option_menu
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



# if st.sidebar.button('Profile', type = 'tertiary'):
#     st.session_state['current_page'] = 'profile'
# if st.sidebar.button('Chat', type = 'tertiary'):
#     st.session_state['current_page'] = 'chat'
# if st.sidebar.button('Planner', type = 'tertiary'):
#     st.session_state['current_page'] = 'planner'
# if st.sidebar.button('Pantry', type = 'tertiary'):
#     st.session_state['current_page'] = 'pantry'
# if st.sidebar.button('Recipes', type = 'tertiary'):
#     st.session_state['current_page'] = 'recipes'




with st.sidebar:
    st.image("smartbites_logo-removebg-preview.png", use_container_width=True)
    st.header("SmartBites")
    st.markdown("__________")
    # st.divider()
    selected = option_menu(
        menu_title= None, 
        # menu_icon= None, 
        options=["Profile", "Chat", "Planner", "Pantry", "Recipes"],
        icons = ["person", "robot", "calendar-week", "basket", "book"],
        default_index=1,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#555", "font-size": "20px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"5px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#e2e2d5", "color": "black"}, # The "pill" effect
        }
    )

page_map = {
    "Profile": "profile",
    "Chat": "chat",
    "Planner": "planner",
    "Pantry": "pantry",
    "Recipes": "recipes"
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
elif st.session_state['current_page'] == 'recipes':
    recipes_page()
    





st.sidebar.empty().write("")  # Add some space

if st.sidebar.button('Logout'):
        auth.logout()
        st.session_state.clear()
        st.rerun()

