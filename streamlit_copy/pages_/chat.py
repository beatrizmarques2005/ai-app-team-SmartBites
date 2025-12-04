import streamlit as st
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.services_old.ai_service import AIService
from src.services_old.document_service import DocumentService
from src.services_old.receipt_service import ReceiptService





def chat_page():
    # Page config
    st.set_page_config(
        page_title="Chat with AI",
        page_icon="🤖",
        layout="centered"
    )

    st.title("Your chat assistant")
    st.write("Ask your chat assistant anything related to cooking, recipes, or meal planning!")

    # Initialize AI client
    try:
        @st.cache_resource
        def get_services():
            ai = AIService()
            receipt = ReceiptService()
            doc = DocumentService()
            return {"ai": ai, "receipt": receipt, "doc": doc}

        services = get_services()

        if 'messages' not in st.session_state:
            st.session_state.messages = []

        # Receipt upload area
        uploaded = st.file_uploader("Upload a receipt (PDF or image)", type=["pdf", "png", "jpg", "jpeg"])

        if uploaded is not None:
            try:
                with st.spinner("Analyzing receipt..."):
                    file_bytes = uploaded.read()
                    mime_type = getattr(uploaded, "type", None) or None
                    analysis = services["receipt"].analyze_receipt(file_bytes, mime_type=mime_type)

                    # Store parsed receipt in session for later chat context
                    st.session_state.last_receipt = analysis

                    st.success("Receipt analyzed")
            except Exception as e:
                st.error(f"Failed to analyze receipt: {e}")

        # Show parsed receipt summary if present
        if 'last_receipt' in st.session_state:
            r = st.session_state.last_receipt
            st.markdown("**Parsed receipt**")
            st.write({
                "store_name": r.get("store_name"),
                "purchase_date": r.get("purchase_date"),
                "total": r.get("total"),
            })
            if items := r.get("items"):
                st.markdown("**Items**")
                for i, item in enumerate(items, 1):
                    st.write(f"{i}. {item.get('name')} — qty: {item.get('quantity')} unit_price: {item.get('unit_price')} total: {item.get('total_price')}")

        # Render existing chat messages
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Chat input - route questions to AI with receipt context when available
        if prompt := st.chat_input("What's on your mind?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar='🥸'):
                st.write(prompt)

            # Build context from last receipt if available
            context = {}
            if 'last_receipt' in st.session_state:
                context['receipt'] = st.session_state.last_receipt

            # Use AIService.answer_question which wraps chat_with_context
            try:
               response = services["ai"].answer_question(prompt, context)
            except Exception:
                # fallback to chat_with_context
                response = services["ai"].chat_with_context(prompt, context)

            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant", avatar='🧑‍🍳'):
                st.write(response)

    except Exception as e:
        st.error(f"Error initializing services: {e}")
        st.info("Make sure your .env file contains GOOGLE_API_KEY and other config variables")

     