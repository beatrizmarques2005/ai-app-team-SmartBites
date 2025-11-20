import streamlit as st
from auth_.login import login_page
from auth_.signup import signup_page
from pages_.profile import profile_page
from pages_.chat import chat_page

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'username' not in st.session_state:
    st.session_state['username'] = ''

if 'show_signup' not in st.session_state:
    st.session_state['show_signup'] = False

if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'profile'


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


st.sidebar.empty().write("")  # Add some space
if st.sidebar.button('Logout'):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.rerun()


if st.session_state['current_page'] == 'profile':
    profile_page()
elif st.session_state['current_page'] == 'chat':
    chat_page()
