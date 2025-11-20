import streamlit as st
# from pages import profile


USER_CREDENTIALS = {
    'bitamima': '2005#!'
}


def login_page():
    st.title('Login to your Smart Bites Page!')

    # username = st.text_input('Username')
    # password = st.text_input('Password', type = 'password')

    # if st.button('Login'):
    #     if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
    #         st.session_state['logged_in'] = True
    #         st.session_state['username'] = username
    #         st.success('Logged in successfully')
    #         # st.rerun()~
    #         # st.switch_page('profile')
        
        # else:
        #     st.error('Invalid credentials')

    with st.form('login_form'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        submitted = st.form_submit_button('Login')

        if submitted:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success('Logged in successfully')
                st.rerun()
            else:
                st.error('Invalid credentials')

    st.markdown('Don\'t have an account?')
    if st.button('Sign Up', type = 'tertiary'):
        st.session_state['show_signup'] = True
        st.rerun()



