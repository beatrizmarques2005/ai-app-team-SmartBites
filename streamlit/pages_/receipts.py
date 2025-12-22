"""
Receipts Analyzer page for the SmartBites Streamlit app.

Purpose:
- Upload and analyze receipt images or PDFs to extract items and details.
- Save extracted items to the user's pantry with quantities via `ReceiptParser`.

UI Flow:
- Configures the page (title, icon, centered layout).
- Auth gate: requires `user_id` in session; redirects to login if missing.
- File uploader accepts PDF and image formats (png, jpg, jpeg).
- On upload, calls `ReceiptParser.analyze_receipt()` to extract items (name, quantity, etc.).
- Displays parsed items as a numbered list.
- "Save to pantry" button calls `ReceiptParser.process_and_store()` to insert into `pantry_items` table.
- Shows success/error messages and any warnings from the save operation.

Session State Keys:
- `user_id`: authenticated user identifier required for pantry data scoping.
- `auth`: `AuthService` instance initialized at module level.
- `ai`: `AIService` instance for potential downstream use.

Database Schema:
- Writes to `pantry_items` table with fields derived from receipt analysis (ingredient_name, quantity, user_id, etc.).

Entry Point:
- `receipts_page()`: renders receipt upload UI and handles analysis/storage workflow.
"""
import streamlit as st
from langfuse import observe
from pathlib import Path
from dotenv import load_dotenv
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.services.ai_service import AIService 
from src.authentication import AuthService
from src.workflows.receipt_parser import ReceiptParser

if "auth" not in st.session_state:
    st.session_state.auth = AuthService()

load_dotenv()

@observe
def receipts_page():
    st.set_page_config(
        page_title="Receipts Analyzer",
        page_icon="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/receipt.svg",
        layout="centered"
    )

    st.title("Receipts Analyzer")
    st.subheader("Analyze and store a receipt")

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

    if "ai" not in st.session_state:
        st.session_state.ai = AIService()
 
    # Receipt upload and analysis
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
                
            if items := analysis.get("items"):
                st.markdown("**Items Found:**")
                for i, item in enumerate(items, 1):
                    st.write(
                        f"{i}. {item.get('name')} — quantity: {item.get('quantity')} "
                    )

            # Save items to pantry
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