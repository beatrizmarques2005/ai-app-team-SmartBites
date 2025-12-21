import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.db.client import supabase

def start_of_week(date):
    return date - timedelta(days=date.weekday())


def fetch_user_recipes(user_id, start_date, end_date):
    """Fetch recipes from database for a date range."""
    if not user_id or not supabase:
        return []
    
    try:
        result = (
            supabase.table("recipes")
            .select("*")
            .eq("user_id", user_id)
            .gte("meal_date", start_date.isoformat())
            .lte("meal_date", end_date.isoformat())
            .order("meal_date", desc=False)
            .execute()
        )
        
        if result.data:
            events = []
            for row in result.data:
                events.append({
                    "date": datetime.fromisoformat(row.get("meal_date")).date(),
                    "title": row.get("recipe_name", "Recipe"),
                    "ingredients": row.get("ingredients", []),
                    "details": row.get("instructions", "No instructions"),
                    "meal_type": row.get("meal_type", "Unknown"),
                    "link": row.get("link", ""),
                })
            return events
        return []
    except Exception as e:
        st.error(f"Error fetching recipes: {str(e)}")
        return []


def weekly_planner_page():
    st.set_page_config(page_title='Weekly Planner', page_icon='📆', layout = 'wide', initial_sidebar_state='collapsed')
    st.title(":material/calendar_month: My Weekly Plan")

    # Check if user is logged in
    if "user_id" not in st.session_state or not st.session_state.user_id:
        st.warning("Please log in to view your meal plan.")
        return
    
    user_id = st.session_state.user_id

    # --- Initialize session state ---
    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0
    if "selected_recipe" not in st.session_state:
        st.session_state.selected_recipe = None
    if "date_search" not in st.session_state:
        st.session_state.date_search = None

    # cola, colb = st.columns([1, 3])
    # with cola:
    #     selected_date = st.date_input("Go to date", value=st.session_state.date_search or datetime.today())
    #     if st.button("Go"):
    #         st.session_state.date_search = selected_date
    #         st.session_state.week_offset = (start_of_week(selected_date) - start_of_week(datetime.today().date())).days // 7
    #         st.session_state.selected_event = None


    st.markdown("")
    st.markdown("")


    nav_col1, nav_col2, nav_col3, nav_spacer, nav_col4 = st.columns([0.5, 1, 0.5, 3, 2])
    
    with nav_col1:
        if st.button(":material/arrow_back:", key="prev", use_container_width=True):
            st.session_state.week_offset -= 1
            st.rerun()
            
    with nav_col2:
        if st.button("This Week", use_container_width=True):
            st.session_state.week_offset = 0
            st.rerun()
            
    with nav_col3:
        if st.button(":material/arrow_forward:", key="next", use_container_width=True):
            st.session_state.week_offset += 1
            st.rerun()

    with nav_col4:
        selected_date = st.date_input("Jump to date", label_visibility="collapsed", value=(st.session_state.date_search or datetime.today().date()))
        if selected_date != st.session_state.date_search:
            st.session_state.date_search = selected_date
            st.session_state.week_offset = (start_of_week(selected_date) - start_of_week(datetime.today().date())).days // 7
            st.rerun()

    st.markdown("")
    st.markdown("")





    # --- Week navigation buttons ---
    # col1, col2, col3, col4  = st.columns(4)
    # if col1.button("**<**", type = 'tertiary'):
    #     st.session_state.week_offset -= 1
    #     st.session_state.selected_event = None
    

    # if col2.button("Current"):
    #     st.session_state.week_offset = 0
    #     st.session_state.selected_event = None

    # if col3.button("**>**", type = 'tertiary'):
    #     st.session_state.week_offset += 1
    #     st.session_state.selected_event = None

    # with col4:
    #     # Date picker should not override arrow navigation unless changed
    #     selected_date = st.date_input(
    #         "🔎",
    #         value=(st.session_state.date_search or datetime.today().date()),
    #         key="planner_date_search",
    #     )
    #     # Initialize once
    #     if st.session_state.date_search is None:
    #         st.session_state.date_search = selected_date
    #     # Only update offset when the user changes the date
    #     if selected_date != st.session_state.date_search:
    #         st.session_state.date_search = selected_date
    #         st.session_state.week_offset = (
    #             start_of_week(selected_date) - start_of_week(datetime.today().date())
    #         ).days // 7
    #         st.session_state.selected_event = None

    # --- Compute week range ---
    # today = datetime.today().date()
    # start_week = start_of_week(today) + timedelta(weeks=st.session_state.week_offset)
    # week_days = [start_week + timedelta(days=i) for i in range(7)]

    # # Fetch recipes for the week (and surrounding days for flexibility)
    # week_start = start_week
    # week_end = start_week + timedelta(days=6)
    # events = fetch_user_recipes(user_id, week_start, week_end)

    # st.subheader(f"Week of {start_week.strftime('%b %d, %Y')}")


    today = datetime.today().date()
    start_week = start_of_week(today) + timedelta(weeks=st.session_state.week_offset)
    end_week = start_week + timedelta(days=6)
    week_days = [start_week + timedelta(days=i) for i in range(7)]
    events = fetch_user_recipes(user_id, start_week, start_week + timedelta(days=6))

    st.markdown(f"### Week of {start_week.strftime('%B %d, %Y')}")
    st.divider()

    # --- Display calendar grid ---
    # cols = st.columns(7)
    # for i, day in enumerate(week_days):
    #     day_events = [e for e in events if e["date"] == day]
    #     with cols[i]:
    #         st.markdown(f"**{day.strftime('%a %d')}**")
    #         for e in day_events:
    #             if st.button(e["title"], key=f"{day}-{e['title']}"):
    #                 st.session_state.selected_event = e


    # --- Display calendar grid ---
    cols = st.columns(7)
    today = datetime.today().date() # Get current date

    for i, day in enumerate(week_days):
        is_today = (day == today)
        
        with cols[i]:
            # If it's today, we start a bordered container to "box" the whole day
            # If not today, we use a ghost container (no border) to keep alignment
            day_box = st.container(border=is_today) 
            
            with day_box:
                # 1. Day Header
            
                
                st.markdown(f"**{day.strftime('%a %d')}**")
                st.divider() # Small line under the date
                
                # 2. Filter events for this day
                day_events = [e for e in events if e["date"] == day]
                
                if not day_events:
                    st.caption("No meals planned")
                
                for e in day_events:
                    # Individual meal cards inside the day box
                    # with st.container(border=True):
                    #     st.caption(f"ID: {e.get('meal_type', 'Meal')}")
                    if st.button(e["title"], key=f"btn-{day}-{e['title']}", use_container_width=True):
                        st.session_state.selected_event = e
                            # st.rerun()




    # cols = st.columns(7)
    # for i, day in enumerate(week_days):
    #     with cols[i]:
    #         # Highlight "Today" with a different style if it falls in the current week
    #         is_today = day == today
    #         day_label = day.strftime('%a %d')
    #         st.markdown(f"<div style='text-align: center; color: {'#C8DDC5' if is_today else 'inherit'}; font-weight: bold;'>{day_label}</div>", unsafe_allow_html=True)
            
    #         day_events = [e for e in events if e["date"] == day]

    #         for e in day_events:
    #             if st.button(e["title"], key=f"{day}-{e['title']}"):
    #                 st.session_state.selected_event = e
                # Use st.container with border for a "Card" look
                # with st.container(border=True):
                #     # Show meal type as a small badge
                #     st.caption(e['meal_type'].upper())
                #     if st.button(e["title"], key=f"{day}-{e['title']}", use_container_width=True):
                #         st.session_state.selected_event = e
                #         st.rerun()

    # ---------- Recipe popup ----------
    if st.session_state.selected_recipe:
        recipe = st.session_state.selected_recipe

        @st.dialog("Recipe Details")
        def show_event_dialog():
            import re
            
            st.subheader(f"🍴 {event['title']}")
            st.markdown(f"**Meal Type:** {event.get('meal_type', 'Unknown')}")
            st.markdown(f"**Date:** {event['date']}")
            
            # Display ingredients as bullet points
            st.markdown(f"**Ingredients:**")
            ingredients = event.get('ingredients')
            if ingredients:
                if isinstance(ingredients, str):
                    # Parse string ingredients
                    ingredient_lines = ingredients.split(',')
                    for ingredient in ingredient_lines:
                        ingredient = ingredient.strip()
                        if ingredient:
                            st.markdown(f"• {ingredient}")
                elif isinstance(ingredients, list):
                    # If it's already a list
                    for ingredient in ingredients:
                        st.markdown(f"• {ingredient}")

            st.markdown(f"**Instructions:**")
            
            # Parse and display instructions as numbered steps
            instructions = event['details']
            
            # Split by pattern like "1. ", "2. ", etc.
            steps = re.split(r'\d+\.\s+', instructions)
            
            # Remove empty first element if split started with a number
            steps = [step.strip() for step in steps if step.strip()]
            
            # Display each step as a bullet point
            for i, step in enumerate(steps, 1):
                st.markdown(f"• **Step {i}:** {step}")
            
            if event.get('link'):
                st.markdown(f"**[View Recipe Link]({event['link']})**")

        show_event_dialog()