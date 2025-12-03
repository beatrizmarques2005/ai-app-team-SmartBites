import streamlit as st
from streamlit_bea._common import get_services

st.set_page_config(page_title='Shopping List - SmartBites')
services = get_services()
shopping = services['shopping']

st.title('Shopping List')
with st.form('add'):
    name = st.text_input('Item name')
    qty = st.number_input('Quantity', min_value=0.0, value=1.0)
    unit = st.text_input('Unit', value='pcs')
    if st.form_submit_button('Add'):
        if not name.strip():
            st.warning('Enter item name')
        else:
            shopping.add_item('demo-user', name.strip(), qty, unit)
            st.success('Added')

items = shopping.list_items('demo-user')
if not items:
    st.info('No shopping items')
else:
    for it in items:
        cols = st.columns([4,1])
        with cols[0]:
            st.write(f"{it.get('name')} — {it.get('quantity')} {it.get('unit')}")
        with cols[1]:
            if st.button('Remove', key=f"rm-{it.get('id')}"):
                shopping.remove_item('demo-user', it.get('id'))
                st.experimental_rerun()
