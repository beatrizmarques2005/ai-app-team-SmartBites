import streamlit as st
from streamlit_bea._common import get_services

st.set_page_config(page_title='Receipts - SmartBites')
services = get_services()
receipt_svc = services['receipt']

st.title('Receipts (demo)')
uploaded = st.file_uploader('Upload receipt (pdf/png/jpg)')
if uploaded is not None:
    try:
        data = receipt_svc.process_and_store_receipt(uploaded.read(), uploaded.type, 'demo-user')
        st.success('Processed (demo)')
        st.json(data)
    except Exception as e:
        st.error(f'Error: {e}')
