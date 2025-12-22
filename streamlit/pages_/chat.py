import streamlit as st
from dotenv import load_dotenv
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.append(project_root)

from src.services.ai_service import AIService 
from src.authentication import AuthService

if "auth" not in st.session_state:
    st.session_state.auth = AuthService()

load_dotenv()

def chat_page():
    st.set_page_config(
        page_title="SmartBites | Chat Bot",
        page_icon="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/robot.svg",
        layout="centered", 
        initial_sidebar_state="collapsed"
    )

    if "user_id" not in st.session_state or not st.session_state.user_id:
        st.switch_page("login.py")

    st.title("Chat Bot")
    st.markdown("Ask me anything about recipes, ingredients, or cooking tips!")
    
    # user_id = st.session_state.get("user_id")

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



    # 2. Render messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑‍🍳" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    # 3. Place the input OUTSIDE (below) the container.
    # Streamlit automatically anchors this to the bottom of the tab area.
    prompt = st.chat_input("Type your message here...", key="chat_input")

    if prompt:
        # Add user message and get response, then rerun to display from history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("SmartBites is cooking..."):
            try:
                response = st.session_state.ai.send_message(st.session_state.chat, prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {e}")
        
        st.rerun()



    # with tab2:
        # st.subheader("Analyze and store a receipt")
        # uploaded = st.file_uploader("Upload a receipt (PDF or image)", type=["pdf", "png", "jpg", "jpeg"])
        # receipt_parser = ReceiptParser()

        # if uploaded is not None:
        #     try:
        #         file_bytes = uploaded.read()
        #         mime_type = getattr(uploaded, "type", None)

        #         with st.spinner("Analyzing receipt..."):
        #             analysis = receipt_parser.analyze_receipt(file_bytes, mime_type=mime_type)

        #         if "error" in analysis:
        #             st.error(f"Analysis error: {analysis['error']}")
        #             st.stop()

        #         # USING AN EXPANDER: This prevents Tab 2 from becoming so long 
        #         # that it pushes the Chat Input in Tab 1 down.
        #         with st.expander("📄 View Parsed Receipt Details", expanded=True):
        #             st.write({
        #                 "store_name": analysis.get("store_name"),
        #                 "purchase_date": analysis.get("purchase_date"),
        #                 "total": analysis.get("total"),
        #             })
                    
        #             if items := analysis.get("items"):
        #                 st.markdown("**Items Found:**")
        #                 for i, item in enumerate(items, 1):
        #                     st.write(
        #                         f"{i}. {item.get('name')} — qty: {item.get('quantity')} "
        #                         f"unit_price: {item.get('unit_price')} total: {item.get('total_price')}"
        #                     )

        #         if st.button("Save to pantry & shopping list", key="save_receipt"):
        #             user_id = st.session_state.get("user_id")
        #             if not user_id:
        #                 st.error("User ID missing; please log in again.")
        #             else:
        #                 try:
        #                     with st.spinner("Saving..."):
        #                         saved = receipt_parser.process_and_store(
        #                             file_bytes, mime_type=mime_type, user_id=user_id
        #                         )
                            
        #                     if "error" in saved:
        #                         st.error(f"Failed to save: {saved['error']}")
        #                     else:
        #                         st.success("Receipt saved successfully!")
        #                         if "pantry_warnings" in saved:
        #                             st.warning("\n".join(saved["pantry_warnings"]))
        #                 except Exception as e:
        #                     st.error(f"Failed to save receipt: {e}")
        #     except Exception as e:
        #         st.error(f"Receipt processing failed: {e}")

    




        # st.subheader("Analyze and store a receipt")
        # uploaded = st.file_uploader("Upload a receipt (PDF or image)", type=["pdf", "png", "jpg", "jpeg"])
        # receipt_parser = ReceiptParser()

        # if uploaded is not None:
        #     try:
        #         file_bytes = uploaded.read()
        #         mime_type = getattr(uploaded, "type", None) # or "application/octet-stream"

        #         # receipt_parser.validate_file(file_bytes, mime_type)

        #         extracted_text = receipt_parser.extract_text(file_bytes, mime_type)

        #         with st.spinner("Analyzing receipt..."):
        #             analysis = receipt_parser.analyze_receipt(file_bytes, mime_type=mime_type)

        #         # Debug: Show any errors
        #         if "error" in analysis:
        #             st.error(f"Analysis error: {analysis['error']}")
        #             st.stop()

        #         # st.session_state.last_receipt = analysis
        #         # st.session_state.last_receipt_file = file_bytes
        #         # st.session_state.last_receipt_mime = mime_type

        #         # with st.expander("Raw extracted text"):
        #         #     st.text_area("", value=extracted_text, height=200)

        #         st.markdown("**Parsed receipt**")
        #         st.write({
        #             "store_name": analysis.get("store_name"),
        #             "purchase_date": analysis.get("purchase_date"),
        #             "total": analysis.get("total"),
        #         })
        #         if items := analysis.get("items"):
        #             st.markdown("**Items**")
        #             for i, item in enumerate(items, 1):
        #                 st.write(
        #                     f"{i}. {item.get('name')} — qty: {item.get('quantity')} "
        #                     f"unit_price: {item.get('unit_price')} total: {item.get('total_price')}"
        #                 )

        #         if st.button("Save to pantry & shopping list", key="save_receipt"):
        #             user_id = st.session_state.get("user_id")
        #             if not user_id:
        #                 st.error("User ID missing; please log in again.")
        #             else:
        #                 try:
        #                     with st.spinner("Saving and updating pantry..."):
        #                         saved = receipt_parser.process_and_store(
        #                             file_bytes, mime_type=mime_type, user_id=user_id
        #                         )
                            
        #                     # Check if save succeeded
        #                     if "error" in saved:
        #                         st.error(f"Failed to save: {saved['error']}")
        #                     else:
        #                         st.success("Receipt saved and pantry/shopping list updated.")
        #                         st.json(saved)
        #                         # Show any warnings
        #                         if "pantry_warnings" in saved:
        #                             st.warning("Some items had issues updating pantry:\n" + "\n".join(saved["pantry_warnings"]))
        #                 except Exception as e:
        #                     st.error(f"Failed to save receipt: {e}")
        #     except Exception as e:
        #         st.error(f"Receipt processing failed: {e}")
