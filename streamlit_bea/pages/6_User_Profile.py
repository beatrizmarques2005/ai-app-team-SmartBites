import streamlit as st
from streamlit_bea._common import get_services

st.set_page_config(page_title='Profile - SmartBites')
use_live = st.sidebar.checkbox('Use live services (Supabase)', value=False)
services = get_services(use_live=use_live)
svc = services['pantry']
user_svc = services.get('user')

st.title('User Profile')
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = 'demo-user'

# Try to fetch live profile when requested
profile = None
if use_live and user_svc:
    try:
        profile = user_svc.get_user_profile(st.session_state['user_id'])
    except Exception:
        profile = None

if not profile:
    profile = st.session_state.get('profile') or {'id': st.session_state['user_id'], 'username': 'demo', 'full_name': 'Demo User', 'diet_type': 'balanced', 'allergies': []}

# Show editable fields
profile['username'] = st.text_input('Username', profile.get('username', ''))
profile['full_name'] = st.text_input('Full name', profile.get('full_name', ''))
profile['email'] = st.text_input('Email', profile.get('email', ''))
profile['diet_type'] = st.text_input('Diet type', profile.get('diet_type', ''))
allergies_val = ','.join(profile.get('allergies', []) if isinstance(profile.get('allergies', []), list) else [profile.get('allergies', '')])
profile['allergies'] = st.text_input('Allergies (comma-separated)', allergies_val)
profile['number_of_members'] = st.number_input('Household members', min_value=1, value=int(profile.get('number_of_members') or 1))

if st.button('Save Profile'):
    # normalize allergies to list
    try:
        profile['allergies'] = [a.strip() for a in (profile.get('allergies') or '').split(',') if a.strip()]
    except Exception:
        profile['allergies'] = profile.get('allergies')

    st.session_state['profile'] = profile
    if use_live and user_svc:
        try:
            user_svc.update_user_profile(st.session_state['user_id'], profile)
            st.success('Profile saved to DB')
        except Exception as e:
            st.warning(f'Profile saved locally, DB save failed: {e}')
    else:
        st.success('Profile saved (session only)')

st.markdown('---')
st.subheader('Raw profile data')
st.json(profile)
