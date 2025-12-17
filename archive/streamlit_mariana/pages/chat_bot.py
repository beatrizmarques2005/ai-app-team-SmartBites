import streamlit as st
from dotenv import load_dotenv
import os

# source_code_path = os.path.abspath(os.path.join("../../src"))
# if source_code_path not in os.sys.path:
#     os.sys.path.append(source_code_path)

import sys
import os

# Calculate the path to the project root: 
# Go up from 'pages' (..), up from 'streamlit_mariana' (..), up from 'ai-app-team-SmartBites' (..) 
# The root is 3 levels up from the current file's directory.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.append(project_root)

# Verify the calculated path (optional)
# print(f"Added to path: {project_root}")

from src.services.ai_service import AIService 
from authentication import AuthService

if "auth" not in st.session_state:
    st.session_state.auth = AuthService()

load_dotenv()

# ai = st.session_state.ai
# chat = st.session_state.chat

st.set_page_config(
    page_title="SmartBites | Chat Bot",
    page_icon="🤖",
    layout="centered"
)

if "user_id" not in st.session_state or not st.session_state.user_id:
    st.switch_page("login.py")

st.title("🤖 SmartBites Chat Bot")
st.markdown("Ask me anything about recipes, ingredients, or cooking tips!")


if "ai" not in st.session_state:
    st.session_state.ai = AIService()

if "chat" not in st.session_state:
    auth = st.session_state.auth
    if auth.get_user_id() is not None:
        st.session_state.chat = st.session_state.ai.create_chat(auth=auth)
    else:
        st.warning("User not logged in properly.")
        st.stop()

if 'messages' not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    avatar = "🧑‍🍳" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message here...", key ="chat_input"):

    with st.chat_message("user", avatar="🧑‍🍳"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("SmartBites is cooking..."):
            try:
                response = st.session_state.ai.send_message(st.session_state.chat, prompt)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Please try again later.")
            



# response = ai.send_message(chat, "Hello from Streamlit!")

# st.write(response.text)

# # ---------- CHAT BOT INTERFACE ----------
# if 'chat' not in st.session_state:
#     st.session_state.chat = ai.client.chat(
#         model = ai.model,
#         config = {'system_instruction': ai.system_instruction,
#                   'temperature': ai.temperature}
#     )


# ---------- LOGOUT BUTTON (ADD THIS AT THE VERY BOTTOM) ----------
st.markdown("---")
if st.button("🚪 Logout"):
    st.session_state.clear()
    st.switch_page("login.py")