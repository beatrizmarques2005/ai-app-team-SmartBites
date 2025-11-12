import streamlit as st

st.set_page_config(page_title='User Profile', page_icon='👤')

st.title('User Profile')
st.subheader('Hello, Francisca!')

col1, col2 = st.columns(2)

with col1:
    st.image('https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.vecteezy.com%2Fpng%2F19879186-user-icon-on-transparent-background&psig=AOvVaw34ut32snAe3ZGUrUbwcA7Y&ust=1762816065872000&source=images&cd=vfe&opi=89978449&ved=0CBIQjRxqFwoTCODuld2X5pADFQAAAAAdAAAAABAJ')


with col2:
    st.markdown(f'**Name**: {st.session_state.username}')
    st.markdown('**Age**: 25')
    st.markdown('**Household Size**: 1')
    st.markdown('**Alergens/Intolerances**: Lactose')
