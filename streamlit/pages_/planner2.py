'''import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar
#pip install streamlit-calendar
#            datetime


def weekly_planner_page():
    st.set_page_config(
        page_title = 'Weekly Planner',
        page_icon = '📆'
    )

    st.title('My Weekly Plan')

    if 'clicked_event_details' not in st.session_state:
        st.session_state['clicked_event_details'] = None

    today = datetime.today()
    events = [
        {'id': 1, 'title': 'soup', "start": (today + timedelta(hours=9)).isoformat(),
        "end": (today + timedelta(hours=10)).isoformat(),  'details': 'Tomato soup with basil', 'clickable': True},
        {'id': 2, 'title': 'salad', 'start': (today + timedelta(hours=12)).isoformat(), "end": (today + timedelta(hours=13)).isoformat(), 'details': 'Caesar salad with croutons', 'clickable': True},
    ]

    calendar_options = {
        'initialView' : 'dayGridWeek',
        'editable' : False,
        'selectable' : True, 
        "eventClick": "function(info) { Streamlit.setComponentValue({clicked_event: info.event.toPlainObject()}); }"
        }

    
    calendar_data = calendar(events = events, options = calendar_options, key = 'my_event_calendar')


    if calendar_data and 'clicked_event' in calendar_data:
        event_clicked = calendar_data['clicked_event']
        clicked_id = event_clicked['id']
        event = next(ev for ev in events if ev['id'] == clicked_id)
        st.session_state['clicked_event_details'] = event

    event_data = st.session_state.get('clicked_event_details')

    if event_data:
        # with st.dialog(f"Event: {event_data['title']}", key=f"dialog_{event_data['id']}"):
        #     st.markdown("---")
        st.subheader(f"Recipe: {event_data['title']}")
        st.write(f"Details: {event_data['details']}")
        st.markdown("---")
            # st.button("Close", key=f"close_{event_data['id']}", on_click=lambda: st.session_state.update({'clicked_event_details': None}))
    else:
        st.info('Click on an event to see the details here.')'''