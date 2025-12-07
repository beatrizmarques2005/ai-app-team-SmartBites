import streamlit as st
from datetime import datetime, timedelta

 # --- Helper function to get start of the week ---
def start_of_week(date):
    return date - timedelta(days=date.weekday())



def weekly_planner_page():
    st.set_page_config(page_title='Weekly Planner', page_icon='📆', layout = 'wide')
    st.title("My Weekly Plan")

    # --- Sample events (replace with your own) ---
    events = [
        {"date": datetime.today().date(), "title": "Soup", "details": "Tomato soup with basil"},
        {"date": datetime.today().date(), "title": "Salad", "details": "Caesar salad with croutons"},
        {"date": datetime.today().date(), "title": "Pasta", "details": "Spaghetti with tomato sauce"},
    ]

    # --- Initialize session state ---
    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0
    if "selected_event" not in st.session_state:
        st.session_state.selected_event = None

    if 'date_search' not in st.session_state:
        st.session_state.date_search = None

    # cola, colb = st.columns([1, 3])
    # with cola:
    #     selected_date = st.date_input("Go to date", value=st.session_state.date_search or datetime.today())
    #     if st.button("Go"):
    #         st.session_state.date_search = selected_date
    #         st.session_state.week_offset = (start_of_week(selected_date) - start_of_week(datetime.today().date())).days // 7
    #         st.session_state.selected_event = None


    # --- Week navigation buttons ---
    col1, col2, col3, col4  = st.columns(4)
    if col1.button("**<**", type = 'tertiary'):
        st.session_state.week_offset -= 1
        st.session_state.selected_event = None
    

    if col2.button("Current"):
        st.session_state.week_offset = 0
        st.session_state.selected_event = None

    if col3.button("**>**", type = 'tertiary'):
        st.session_state.week_offset += 1
        st.session_state.selected_event = None

    with col4:
        selected_date = st.date_input("🔎", value=st.session_state.date_search or datetime.today())
        if selected_date:
            # selected_date = st.date_input("Go to date", value=st.session_state.date_search or datetime.today())
            st.session_state.date_search = selected_date
            st.session_state.week_offset = (start_of_week(selected_date) - start_of_week(datetime.today().date())).days // 7
            st.session_state.selected_event = None

    # --- Compute week range ---
    today = datetime.today().date()
    start_week = start_of_week(today) + timedelta(weeks=st.session_state.week_offset)
    week_days = [start_week + timedelta(days=i) for i in range(7)]

    st.subheader(f"Week of {start_week.strftime('%b %d, %Y')}")

    # --- Display calendar grid ---
    cols = st.columns(7)
    for i, day in enumerate(week_days):
        day_events = [e for e in events if e["date"] == day]
        with cols[i]:
            st.markdown(f"**{day.strftime('%a %d')}**")
            for e in day_events:
                if st.button(e["title"], key=f"{day}-{e['title']}"):
                    st.session_state.selected_event = e

    # --- Modal-style pop-up for event details ---
    if st.session_state.selected_event:
        event = st.session_state.selected_event

        @st.dialog("Details")
        def show_event_dialog():
            st.subheader(f"🍴 {event['title']}")
            st.markdown(f"**Details:** {event['details']}")
            


        show_event_dialog()