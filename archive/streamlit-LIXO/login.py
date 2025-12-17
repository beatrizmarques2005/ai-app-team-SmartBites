import streamlit as st
from pages import profile




USER_CREDENTIALS = {
    'bitamima': '2005#!'
}

st.set_page_config(page_title='Login', initial_sidebar_state = 'collapsed', layout = 'centered')

# def login_page():
st.title('Login to your Smart Bites Page!')

username = st.text_input('Username')
password = st.text_input('Password', type = 'password')

if st.button('Login'):
    if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.success('Logged in successfully')
        # st.rerun()~
        profile.profile_page()
        
    
    else:
        st.error('Invalid credentials')

st.markdown('Don\'t have an account?')
if st.button('Sign Up', type = 'tertiary'):
    st.markdown('Sign Up functionality is not implemented yet.')
