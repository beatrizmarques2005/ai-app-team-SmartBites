import streamlit as st

# If the user is not logged in, send to login page
if "user_id" not in st.session_state:
    st.switch_page("pages/login.py")

st.title("SmartBites")
st.write("Welcome to SmartBites!")
