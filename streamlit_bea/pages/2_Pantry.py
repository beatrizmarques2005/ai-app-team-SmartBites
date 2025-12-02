import streamlit as st
from streamlit_bea._common import get_services

st.set_page_config(page_title='Pantry - SmartBites')
use_live = st.sidebar.checkbox('Use live services (Supabase)', value=False)
services = get_services(use_live=use_live)
svc = services['pantry']

st.title('Pantry')
with st.expander('Add item'):
    with st.form('add'):
        name = st.text_input('Item name')
        qty = st.number_input('Quantity', min_value=0.0, value=1.0)
        unit = st.text_input('Unit', value='pcs')
        if st.form_submit_button('Add'):
            if not name.strip():
                st.warning('Enter item name')
            else:
                try:
                    svc.add_or_update_item('demo-user', name.strip(), float(qty), unit or None)
                    st.success('Added')
                except Exception:
                    # fallback to adapter mock
                    try:
                        svc.adapter.upsert_pantry_item('demo-user', name.strip(), name.strip().lower(), float(qty), unit or None)
                        st.success('Added (adapter fallback)')
                    except Exception as e:
                        st.error(f'Failed to add item: {e}')

# Fetch items from service (live or mock)
try:
    items = svc.list_items('demo-user')
except Exception:
    # fallback to adapter storage if present
    try:
        items = list(getattr(svc, 'adapter')._data)
    except Exception:
        items = []

if not items:
    st.info('No items in pantry yet')
else:
    for it in items:
        cols = st.columns([4,1,1])
        with cols[0]:
            st.write(f"{it.get('name')} — {it.get('quantity')} {it.get('unit')}")
        with cols[1]:
            if st.button('Inc', key=f"inc-{it.get('id')}"):
                try:
                    svc.add_or_update_item('demo-user', it.get('name'), (it.get('quantity') or 0) + 1, it.get('unit'))
                except Exception:
                    try:
                        svc.adapter.upsert_pantry_item('demo-user', it.get('name'), it.get('normalized_name') or it.get('name').lower(), 1, it.get('unit'))
                    except Exception:
                        st.error('Unable to increment item')
                st.experimental_rerun()
        with cols[2]:
            if st.button('Remove', key=f"rem-{it.get('id')}"):
                removed = False
                # try service removal methods
                for fn in ('remove_item', 'delete_item', 'delete_pantry_item'):
                    try:
                        method = getattr(svc, fn)
                        # many implementations accept (user_id, item_id) or (item_id)
                        try:
                            removed = method('demo-user', it.get('id'))
                        except TypeError:
                            removed = method(it.get('id'))
                        if removed:
                            break
                    except Exception:
                        removed = False

                if not removed:
                    try:
                        removed = svc.adapter.delete_pantry_item(it.get('id'))
                    except Exception:
                        removed = False

                if removed:
                    st.experimental_rerun()
