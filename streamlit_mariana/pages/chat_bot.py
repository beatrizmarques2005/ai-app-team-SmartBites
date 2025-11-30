import streamlit as st

if "user_id" not in st.session_state or not st.session_state.user_id:
    st.switch_page("login.py")

st.title("🤖 SmartBites Chat Bot")
st.info("Chat bot coming soon...")


# ---------- LOGOUT BUTTON (ADD THIS AT THE VERY BOTTOM) ----------
st.markdown("---")
if st.button("🚪 Logout"):
    st.session_state.clear()
    st.switch_page("login.py")