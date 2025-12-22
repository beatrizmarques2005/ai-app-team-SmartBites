"""
Chat page for the SmartBites Streamlit app.

Purpose:
- Provide a conversational interface for recipe, ingredient, and cooking questions.

UI Flow:
- Configures the page (title, icon, centered layout, collapsed sidebar).
- Initializes `AIService` in session and creates a chat session via `AIService.create_chat()`.
- Renders past messages using `st.chat_message`.
- Captures new input with `st.chat_input`, sends it to the AI, appends the response, then `st.rerun()`.

Session State Keys:
- `auth`: `AuthService` instance; must provide a valid `user_id`.
- `user_id`: authenticated user identifier used for routing and scoping chat.
- `ai`: `AIService` instance used to send/receive messages.
- `chat`: handle/object returned by `AIService.create_chat()` for the active session.
- `messages`: list of `{role, content}` dicts representing chat history.
- `chat_input`: Streamlit-managed key for the chat input widget.

Entry Point:
- `chat_page()`: renders the chat UI and handles message send/receive lifecycle.
"""

import streamlit as st
from langfuse import observe
from dotenv import load_dotenv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.services.ai_service import AIService 
from src.authentication import AuthService

if "auth" not in st.session_state:
    st.session_state.auth = AuthService()

load_dotenv()

@observe
def chat_page():
    st.set_page_config(
        page_title="SmartBites | Chat Bot",
        page_icon="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/robot.svg",
        layout="centered", 
        initial_sidebar_state="collapsed"
    )
    st.title("Chat Bot")
    st.markdown("Ask me anything about recipes, ingredients, or cooking tips!")

    if "ai" not in st.session_state:
        st.session_state.ai = AIService()

    auth = st.session_state.auth

    if "chat" not in st.session_state:
        if auth.get_user_id() is not None:
            st.session_state.chat = st.session_state.ai.create_chat(auth=auth)
        else:
            st.warning("User not logged in properly.")
            st.stop()

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑‍🍳" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Type your message here...", key="chat_input"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("SmartBites is cooking..."):
            try:
                response = st.session_state.ai.send_message(st.session_state.chat, prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {e}")
        
        st.rerun()  