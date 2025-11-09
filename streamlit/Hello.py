import streamlit as st

st.set_page_config(page_title='SmartBites', page_icon='🍽️',  initial_sidebar_state = "collapsed")

st.title('Welcome to SmartBites! 🍽️')
st.header("Cook smarter. Save time. Eat well.")

st.markdown(
    """
    <style>
    /* Page background */
    .stApp {
        background-color: #9dbd9e;
    }
    """, unsafe_allow_html=True)

st.text('Hellooo')