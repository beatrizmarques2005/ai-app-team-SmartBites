import streamlit as st
from streamlit_bea._common import get_services

st.set_page_config(page_title='Chatbot - SmartBites')

use_live = st.sidebar.checkbox('Use live services (Supabase)', value=False)
services = get_services(use_live=use_live)
receipt_svc = services['receipt']
pantry_svc = services['pantry']
user_svc = services.get('user')

st.title('Chatbot')
st.write('Ask questions about your pantry or receipts (demo). Upload a receipt image/PDF and then ask questions about it.')


if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []


for msg in st.session_state['chat_history']:
    role = msg.get('role', 'user')
    text = msg.get('text', '')
    if role == 'user':
        st.markdown(f"**You:** {text}")
    else:
        st.markdown(f"**Assistant:** {text}")


def simple_receipt_answer(receipt: dict, question: str) -> str:
    q = (question or '').lower()
    if not receipt:
        return "No receipt data available. Upload a receipt to ask about it."

    # direct total question
    if 'total' in q or 'how much' in q or 'amount' in q:
        if receipt.get('total') is not None:
            return f"Total on receipt: {receipt.get('total')}"
        return "I couldn't find a total value in the receipt data."

    # list items
    if 'items' in q or 'what' in q and 'buy' in q or 'bought' in q:
        names = [i.get('name') for i in receipt.get('items', [])]
        if not names:
            return 'No individual items found on the receipt.'
        return 'Items: ' + ', '.join(names)

    # quantity of a specific item
    if 'how many' in q or 'quantity' in q or 'count' in q:
        # naive lookup for item name in question
        for item in receipt.get('items', []):
            name = (item.get('name') or '').lower()
            if name and name in q:
                return f"{item.get('name')}: {item.get('quantity', 'unknown')} {item.get('unit', '')}"
        return "I couldn't match an item name in your question. Try asking 'How many eggs' or 'Quantity of milk'."

    # fallback summary
    items = receipt.get('items', [])
    return f"Receipt from {receipt.get('store_name', 'unknown')} on {receipt.get('purchase_date', '')}. {len(items)} items recorded."


# Receipt upload / analysis
uploaded = st.file_uploader('Upload receipt (pdf/png/jpg)', type=['pdf', 'png', 'jpg', 'jpeg'])
if uploaded is not None:
    try:
        raw = uploaded.read()
        # store raw bytes so image can be shown later
        st.session_state['last_receipt_raw'] = raw
        st.session_state['last_receipt_mime'] = uploaded.type

        # prefer process_and_store if available to mirror App.py behavior
        if hasattr(receipt_svc, 'process_and_store_receipt'):
            data = receipt_svc.process_and_store_receipt(raw, uploaded.type, 'demo-user')
        elif hasattr(receipt_svc, 'analyze_receipt'):
            data = receipt_svc.analyze_receipt(raw, uploaded.type)
        else:
            data = {'items': [], 'total': None}

        st.success('Receipt analyzed (demo)')
        st.json(data)
        st.session_state['last_receipt'] = data
    except Exception as e:
        st.error(f'Failed to analyze receipt: {e}')


question = st.text_input('Your question')
if st.button('Send'):
    if not question.strip():
        st.warning('Enter a question')
    else:
        st.session_state['chat_history'].append({'role': 'user', 'text': question})

        # Build context: include last receipt and pantry snapshot
        ctx = {
            'pantry': pantry_svc.list_items('demo-user'),
            'receipt': st.session_state.get('last_receipt'),
            'receipt_raw': st.session_state.get('last_receipt_raw'),
            'receipt_mime': st.session_state.get('last_receipt_mime'),
        }

        # display the uploaded image together with the question if present
        if ctx.get('receipt_raw') and (ctx.get('receipt_mime') or '').startswith('image'):
            try:
                st.image(ctx.get('receipt_raw'), caption='Uploaded receipt', use_column_width=True)
            except Exception:
                pass

        # Try to use a centralized AI QA if available (ReceiptService.ai_service.answer_question)
        answer = None
        try:
            if hasattr(receipt_svc, 'ai_service') and hasattr(receipt_svc.ai_service, 'answer_question'):
                # pass the raw image bytes as part of the context if model/service supports multimodal inputs
                answer = receipt_svc.ai_service.answer_question(question, ctx, system_instruction='You are an assistant answering questions about receipts and pantry data. Answer concisely.')
        except Exception:
            answer = None

        # Fallback: simple rule-based receipt QA
        if not answer:
            answer = simple_receipt_answer(ctx.get('receipt') or {}, question)

        st.session_state['chat_history'].append({'role': 'assistant', 'text': answer})
        st.experimental_rerun()
