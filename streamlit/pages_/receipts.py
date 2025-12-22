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
from src.workflows.receipt_parser import ReceiptParser

if "auth" not in st.session_state:
    st.session_state.auth = AuthService()

load_dotenv()


def receipts_page():
    st.set_page_config(
        page_title="Receipts Analyzer",
        page_icon="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/robot.svg",
        layout="centered"
    )

    if "user_id" not in st.session_state or not st.session_state.user_id:
        st.switch_page("login.py")

    user_id = st.session_state.get('user_id', None)
    if user_id is None:
        st.error("User not logged in.")
        return 
    
    auth = st.session_state.get('auth', None)
    if auth is None:
        st.error("Authentication service not available.")
        return

    st.title("Receipts Analyzer")
    
    if "ai" not in st.session_state:
        st.session_state.ai = AIService()

    st.subheader("Analyze and store a receipt")
    uploaded = st.file_uploader("Upload a receipt (PDF or image)", type=["pdf", "png", "jpg", "jpeg"], )
    receipt_parser = ReceiptParser()

    if uploaded is not None:
        try:
            file_bytes = uploaded.read()
            mime_type = getattr(uploaded, "type", None)

            with st.spinner("Analyzing receipt..."):
                analysis = receipt_parser.analyze_receipt(file_bytes, mime_type=mime_type)

            if "error" in analysis:
                st.error(f"Analysis error: {analysis['error']}")
                st.stop()

            # USING AN EXPANDER: This prevents Tab 2 from becoming so long 
            # that it pushes the Chat Input in Tab 1 down.
                # st.write({
                #     "store_name": analysis.get("store_name"),
                #     "purchase_date": analysis.get("purchase_date"),
                #     "total": analysis.get("total"),
                # })
                
            if items := analysis.get("items"):
                st.markdown("**Items Found:**")
                for i, item in enumerate(items, 1):
                    st.write(
                        f"{i}. {item.get('name')} — quantity: {item.get('quantity')} "
                    )

            if st.button("Save to pantry", key="save_receipt"):
                user_id = st.session_state.get("user_id")
                if not user_id:
                    st.error("User ID missing; please log in again.")
                else:
                    try:
                        with st.spinner("Saving..."):
                            saved = receipt_parser.process_and_store(
                                file_bytes, mime_type=mime_type, user_id=user_id
                            )
                        
                        if "error" in saved:
                            st.error(f"Failed to save: {saved['error']}")
                        else:
                            st.success("Receipt saved successfully!")
                            if "pantry_warnings" in saved:
                                st.warning("\n".join(saved["pantry_warnings"]))
                    except Exception as e:
                        st.error(f"Failed to save receipt: {e}")
        except Exception as e:
            st.error(f"Receipt processing failed: {e}")