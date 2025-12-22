import streamlit as st
from datetime import datetime, timedelta, date
from pathlib import Path
import sys
import calendar

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


def shift_month(base_date: date, delta: int) -> date:
    """Shift a date by delta months, keeping day clamped to month length."""
    y, m = base_date.year, base_date.month
    new_m_index = (m - 1) + delta
    new_y = y + new_m_index // 12
    new_m = (new_m_index % 12) + 1
    last_day = calendar.monthrange(new_y, new_m)[1]
    return date(new_y, new_m, min(base_date.day, last_day))


def month_bounds(base_date: date, month_offset: int):
    """Return first and last date of the month after applying offset."""
    start = shift_month(base_date.replace(day=1), month_offset)
    last_day = calendar.monthrange(start.year, start.month)[1]
    end = date(start.year, start.month, last_day)
    return start, end


def month_weeks(start: date):
    """Build calendar weeks for a month starting at the given date."""
    weeks = []
    cal = calendar.Calendar(firstweekday=0)  # Monday=0 in datetime, but calendar default is Monday=0? Actually 0=Monday? In calendar, 0=Monday.
    for week in cal.monthdatescalendar(start.year, start.month):
        weeks.append(list(week))
    return weeks


def weekly_planner_page():
    st.set_page_config(page_title='SmartBites | Weekly Planner', page_icon='📆', layout = 'wide', initial_sidebar_state='collapsed')
    st.title("My Weekly Plan")

    # Check if user is logged in
    if "user_id" not in st.session_state or not st.session_state.user_id:
        st.warning("Please log in to view your meal plan.")
        return
    
    user_id = st.session_state.user_id

    # --- Initialize session state ---
    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0
    if "month_offset" not in st.session_state:
        st.session_state.month_offset = 0
    if "selected_recipe" not in st.session_state:
        st.session_state.selected_recipe = None
    if "date_search" not in st.session_state:
        st.session_state.date_search = None
    if "planner_view" not in st.session_state:
        st.session_state.planner_view = "Weekly"

    # cola, colb = st.columns([1, 3])
    # with cola:
    #     selected_date = st.date_input("Go to date", value=st.session_state.date_search or datetime.today())
    #     if st.button("Go"):
    #         st.session_state.date_search = selected_date
    #         st.session_state.week_offset = (start_of_week(selected_date) - start_of_week(datetime.today().date())).days // 7
    #         st.session_state.selected_event = None


    st.markdown("")

    today = datetime.today().date()
    # Navigation row with view switch in an expander next to the date search slot
    nav_col1, nav_col2, nav_col3, nav_spacer, nav_col4, nav_col5 = st.columns([0.5, 1, 0.5, 3, 2, 1.2])
    current_view = st.session_state.get("planner_view", "Weekly")
    with nav_col5:
        selection = st.selectbox(
            "View",
            ["Weekly", "Monthly"],
            index=0 if current_view == "Weekly" else 1,
            label_visibility="collapsed",
            key="planner_view_select",
        )
        if selection != current_view:
            st.session_state.planner_view = selection
            st.session_state.selected_recipe = None
            st.session_state.dialog_open = False
            st.rerun()
        else:
            st.session_state.planner_view = selection
            current_view = selection

    if current_view == "Weekly":
        with nav_col1:
            if st.button(":material/arrow_back:", key="prev_week", use_container_width=True):
                st.session_state.week_offset -= 1
                st.session_state.selected_recipe = None
                st.session_state.dialog_open = False
                st.rerun()
        with nav_col2:
            if st.button("This Week", use_container_width=True):
                st.session_state.week_offset = 0
                st.session_state.selected_recipe = None
                st.session_state.dialog_open = False
                st.rerun()
        with nav_col3:
            if st.button(":material/arrow_forward:", key="next_week", use_container_width=True):
                st.session_state.week_offset += 1
                st.session_state.selected_recipe = None
                st.session_state.dialog_open = False
                st.rerun()
        with nav_col4:
            selected_date = st.date_input("Jump to date", label_visibility="collapsed", value=(st.session_state.date_search or today))
            if selected_date != st.session_state.date_search:
                st.session_state.date_search = selected_date
                st.session_state.week_offset = (start_of_week(selected_date) - start_of_week(today)).days // 7
                st.session_state.selected_recipe = None
                st.session_state.dialog_open = False
                st.rerun()

        st.markdown("")

        start_week = start_of_week(today) + timedelta(weeks=st.session_state.week_offset)
        week_days = [start_week + timedelta(days=i) for i in range(7)]
        events = fetch_user_recipes(user_id, start_week, start_week + timedelta(days=6))

        st.markdown(f"### Week {start_week.isocalendar()[1]} ")
        st.divider()

        cols = st.columns(7)
        for i, day in enumerate(week_days):
            is_today = (day == today)
            with cols[i]:
                header_bg = "#eef8ef" if is_today else "transparent"
                header_color = "#0f6716" if is_today else "inherit"
                st.markdown(
                    f"<div style='text-align: center; font-weight: bold; color: {header_color}; background:{header_bg}; border-radius:6px; padding:4px;'>"
                    f"{day.strftime('%a %d')}</div>",
                    unsafe_allow_html=True,
                )
                st.divider()
                day_events = [e for e in events if e["date"] == day]
                if not day_events:
                    st.caption("No meals planned")
                for e in day_events:
                    if st.button(e["title"], key=f"btn-{day}-{e['title']}", use_container_width=True):
                        st.session_state.selected_recipe = e
                        st.session_state.dialog_open = False
                        st.rerun()

    else:
        # Monthly view
        with nav_col1:
            if st.button(":material/arrow_back:", key="prev_month", use_container_width=True):
                st.session_state.month_offset -= 1
                st.session_state.selected_recipe = None
                st.session_state.dialog_open = False
                st.rerun()
        with nav_col2:
            if st.button("This Month", use_container_width=True):
                st.session_state.month_offset = 0
                st.session_state.selected_recipe = None
                st.session_state.dialog_open = False
                st.rerun()
        with nav_col3:
            if st.button(":material/arrow_forward:", key="next_month", use_container_width=True):
                st.session_state.month_offset += 1
                st.session_state.selected_recipe = None
                st.session_state.dialog_open = False
                st.rerun()

        month_start, month_end = month_bounds(today, st.session_state.month_offset)
        events = fetch_user_recipes(user_id, month_start, month_end)
        st.markdown(f"### {month_start.strftime('%B %Y')} ")

        # Weekday header
        header_cols = st.columns(7)
        for idx, wd in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            header_cols[idx].markdown(f"<div style='text-align: center; font-weight: bold;'>{wd}</div>", unsafe_allow_html=True)

        weeks = month_weeks(month_start)
        for week in weeks:
            row_cols = st.columns(7)
            for col, day in zip(row_cols, week):
                in_month = (day.month == month_start.month)
                is_today = (day == today)
                with col:
                    color = "inherit" if in_month else "#bfbfbf"
                    header_bg = "#eef8ef" if is_today else "transparent"
                    header_color = "#0f6716" if is_today else color
                    st.markdown(
                        f"<div style='text-align: center; color: {header_color}; font-weight: bold; background:{header_bg}; border-radius:6px; padding:4px;'>"
                        f"{day.day}</div>",
                        unsafe_allow_html=True,
                    )
                    if in_month:
                        day_events = [e for e in events if e["date"] == day]
                        if not day_events:
                            st.caption("No meals")
                        for e in day_events:
                            if st.button(e["title"], key=f"m-{day}-{e['title']}", use_container_width=True):
                                st.session_state.selected_recipe = e
                                st.session_state.dialog_open = False
                                st.rerun()




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
    if st.session_state.get("selected_recipe") and not st.session_state.get("dialog_open", False):
        st.session_state.dialog_open = True
        recipe = st.session_state.selected_recipe

        @st.dialog("Recipe Details")
        def show_event_dialog():
            import re
            
            st.subheader(f"🍴 {recipe['title']}")
            st.markdown(f"**Meal Type:** {recipe.get('meal_type', 'Unknown')}")
            st.markdown(f"**Date:** {recipe['date']}")
            
            # Display ingredients as bullet points
            st.markdown(f"**Ingredients:**")
            ingredients = recipe.get('ingredients')
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
            instructions = recipe['details']
            
            # Split by pattern like "1. ", "2. ", etc.
            steps = re.split(r'\d+\.\s+', instructions)
            
            # Remove empty first element if split started with a number
            steps = [step.strip() for step in steps if step.strip()]
            
            # Display each step as a bullet point
            for i, step in enumerate(steps, 1):
                st.markdown(f"• **Step {i}:** {step}")
            
            if recipe.get('link'):
                st.markdown(f"**[View Recipe Link]({recipe['link']})**")

            # Close button to clear state and prevent auto re-open
            # if st.button("Close"):
            #     st.session_state.selected_recipe = None
            #     st.session_state.dialog_open = False
            #     st.rerun()

        show_event_dialog()
        