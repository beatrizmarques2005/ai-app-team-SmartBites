import streamlit as st
from dotenv import load_dotenv
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.append(project_root)

# Verify the calculated path (optional)
# print(f"Added to path: {project_root}")

from src.services.ai_service import AIService 
from src.services.auth_service import AuthService

if "auth" not in st.session_state:
    st.session_state.auth = AuthService()

load_dotenv()

# ai = st.session_state.ai
# chat = st.session_state.chat

def chat_page():
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

    tab1, tab2 = st.tabs(["Chat Bot", "Rceipt Analyzer"])
    with tab2:
        uploaded = st.file_uploader("Upload a receipt (PDF or image)", type=["pdf", "png", "jpg", "jpeg"])

        # if uploaded is not None:
        #     try:
        #         with st.spinner("Analyzing receipt..."):
        #             file_bytes = uploaded.read()
        #             mime_type = getattr(uploaded, "type", None) or None
        #             analysis = services["receipt"].analyze_receipt(file_bytes, mime_type=mime_type)

        #             # Store parsed receipt in session for later chat context
        #             st.session_state.last_receipt = analysis

        #             st.success("Receipt analyzed")
        #     except Exception as e:
        #         st.error(f"Failed to analyze receipt: {e}")

        # # Show parsed receipt summary if present
        # if 'last_receipt' in st.session_state:
        #     r = st.session_state.last_receipt
        #     st.markdown("**Parsed receipt**")
        #     st.write({
        #         "store_name": r.get("store_name"),
        #         "purchase_date": r.get("purchase_date"),
        #         "total": r.get("total"),
        #     })
        #     if items := r.get("items"):
        #         st.markdown("**Items**")
        #         for i, item in enumerate(items, 1):
        #             st.write(f"{i}. {item.get('name')} — qty: {item.get('quantity')} unit_price: {item.get('unit_price')} total: {item.get('total_price')}")

       

        
        
        
        
        with tab1:
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





# import streamlit as st


# def chat_page():
#     # Page config
#     st.set_page_config(
#         page_title="Chat with AI",
#         page_icon="🤖",
#         layout="centered"
#     )

#     st.title("Your chat assistant")
#     st.write("Ask your chat assistant anything related to cooking, recipes, or meal planning!")

#     # Initialize AI client
#     try:
#         @st.cache_resource
#         def get_services():
#             ai = AIService()
#             receipt = ReceiptService()
#             doc = DocumentService()
#             return {"ai": ai, "receipt": receipt, "doc": doc}

#         services = get_services()

#         if 'messages' not in st.session_state:
#             st.session_state.messages = []

#         # Receipt upload area
#         uploaded = st.file_uploader("Upload a receipt (PDF or image)", type=["pdf", "png", "jpg", "jpeg"])

#         if uploaded is not None:
#             try:
#                 with st.spinner("Analyzing receipt..."):
#                     file_bytes = uploaded.read()
#                     mime_type = getattr(uploaded, "type", None) or None
#                     analysis = services["receipt"].analyze_receipt(file_bytes, mime_type=mime_type)

#                     # Store parsed receipt in session for later chat context
#                     st.session_state.last_receipt = analysis

#                     st.success("Receipt analyzed")
#             except Exception as e:
#                 st.error(f"Failed to analyze receipt: {e}")

#         # Show parsed receipt summary if present
#         if 'last_receipt' in st.session_state:
#             r = st.session_state.last_receipt
#             st.markdown("**Parsed receipt**")
#             st.write({
#                 "store_name": r.get("store_name"),
#                 "purchase_date": r.get("purchase_date"),
#                 "total": r.get("total"),
#             })
#             if items := r.get("items"):
#                 st.markdown("**Items**")
#                 for i, item in enumerate(items, 1):
#                     st.write(f"{i}. {item.get('name')} — qty: {item.get('quantity')} unit_price: {item.get('unit_price')} total: {item.get('total_price')}")

#         # Render existing chat messages
#         for msg in st.session_state.messages:
#             with st.chat_message(msg["role"]):
#                 st.write(msg["content"])

#         # Chat input - route questions to AI with receipt context when available
#         if prompt := st.chat_input("What's on your mind?"):
#             st.session_state.messages.append({"role": "user", "content": prompt})
#             with st.chat_message("user", avatar='🥸'):
#                 st.write(prompt)

#             # Build context from last receipt if available
#             context = {}
#             if 'last_receipt' in st.session_state:
#                 context['receipt'] = st.session_state.last_receipt

#             # Use AIService.answer_question which wraps chat_with_context
#             try:
#                response = services["ai"].answer_question(prompt, context)
#             except Exception:
#                 # fallback to chat_with_context
#                 response = services["ai"].chat_with_context(prompt, context)

#             st.session_state.messages.append({"role": "assistant", "content": response})
#             with st.chat_message("assistant", avatar='🧑‍🍳'):
#                 st.write(response)

#     except Exception as e:
#         st.error(f"Error initializing services: {e}")
#         st.info("Make sure your .env file contains GOOGLE_API_KEY and other config variables")

     