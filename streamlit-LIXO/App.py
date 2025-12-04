import streamlit as st
from login import login_page

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    
if not st.session_state['logged_in']:
    login_page()
    st.stop()

else:
    st.sidebar.title(f'Welcome, {st.session_state.username}!')
    if st.sidebar.button('Logout'):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.rerun()


        
# st.set_page_config(page_title='SmartBites', page_icon='🍽️',  initial_sidebar_state = "collapsed")

# st.title('Welcome to SmartBites! 🍽️')
# st.header("Cook smarter. Save time. Eat well.")

# st.markdown(
#     """
#     <style>
#     /* Page background */
#     .stApp {
#         background-color: #9dbd9e;
#     }
#     """, unsafe_allow_html=True)

# st.text('Hellooo')