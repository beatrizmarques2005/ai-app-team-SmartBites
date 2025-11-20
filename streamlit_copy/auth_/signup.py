import streamlit as st
from auth_.login import USER_CREDENTIALS  # share the same dict

def signup_page():
    st.title("Sign Up for Smart Bites")

    with st.form("signup_form"):
        new_username = st.text_input("Choose a username")
        new_password = st.text_input("Choose a password", type="password")
        confirm_password = st.text_input("Confirm password", type="password")

        submitted = st.form_submit_button("Sign Up")

        if submitted:
            if new_username in USER_CREDENTIALS:
                st.error("Username already exists.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif new_username == "" or new_password == "":
                st.error("Please fill in all fields.")
            else:
                # Add user to credentials
                USER_CREDENTIALS[new_username] = new_password
                st.success("Account created successfully! Please log in.")
                st.session_state['logged_in'] = True
                st.session_state['username'] = new_username
                st.session_state['show_signup'] = False
                st.rerun()