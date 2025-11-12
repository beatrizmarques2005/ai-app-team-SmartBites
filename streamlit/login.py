import streamlit as st


USER_CREDENTIALS = {
    'bitamima': '2005#!'
}


def login_page():
    st.title('Login to your Smart Bites Page!')

    username = st.text_input('Username')
    password = st.text_input('Password', type = 'password')

    if st.button('Login'):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success('Logged in successfully')
            st.rerun()
        
        else:
            st.error('Invalid credentials')
