import streamlit as st

def profile_page():
    st.set_page_config(page_title='User Profile', page_icon='👤')

    st.title('User Profile')
    st.subheader(f'Hello, {st.session_state.username}!')
    col1, col2 = st.columns(2)

    with col1:
        st.image('https://static.vecteezy.com/system/resources/previews/019/879/186/original/user-icon-on-transparent-background-free-png.png')


    with col2:
        st.markdown(f'**Name**: {st.session_state.username}')
        st.markdown('**Age**: 20')
        st.markdown('**Household Size**: 2')
        st.markdown('**Alergens/Intolerances**: Lactose')
