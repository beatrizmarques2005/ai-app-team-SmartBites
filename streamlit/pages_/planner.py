"""
Planner page for the SmartBites Streamlit app.

Purpose:
- Visualize a user's meal plan in Weekly and Monthly views.
- Navigate across weeks/months and view recipe details saved in the database.

UI Flow:
- Configures the page (title, icon, wide layout, collapsed sidebar).
- Auth gate: requires `user_id` in session; otherwise shows a warning and stops.
- View selector toggles between Weekly and Monthly modes.
- Weekly: prev/next week buttons, "This Week", and a date jump; shows 7-day columns with recipe buttons.
- Monthly: prev/next month buttons and "This Month"; shows a calendar grid with recipe buttons per day.
- Clicking a recipe opens a dialog with title, meal type, date, ingredients, parsed instructions, and an optional link.

Session State Keys:
- `user_id`: identifies the authenticated user for data scoping.
- `planner_view`: current view mode, either "Weekly" or "Monthly".
- `week_offset`, `month_offset`: integers tracking navigation offsets.
- `date_search`: selected date for jumping in Weekly view.
- `selected_recipe`: the recipe dict selected for the details dialog.
- `dialog_open`: bool to prevent the dialog from re-opening every rerun.

Database Schema:
- Reads from `recipes` using fields: `user_id`, `meal_date`, `recipe_name`,
  `ingredients`, `instructions`, `meal_type`, `link`.

Entry Point:
- `weekly_planner_page()`: renders planner UI and hooks recipe dialogs.
"""
import streamlit as st
from langfuse import observe
from datetime import datetime, timedelta, date
from pathlib import Path
import sys
import calendar
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.db.client import supabase
from src.authentication import AuthService

@observe
def start_of_week(date):
    return date - timedelta(days=date.weekday())

@observe
def fetch_user_recipes(user_id, start_date, end_date):
    """Fetch recipes from database for a date range.
    
    Args:
        user_id: The user's unique identifier.
        start_date: Start of date range (date object).
        end_date: End of date range (date object).
    
    Returns:
        list: List of recipe dicts with keys: date, title, ingredients, details, meal_type, link.
              Returns empty list on error or if no recipes found.
    """
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

@observe
def shift_month(base_date: date, delta: int) -> date:
    """Shift a date by delta months, keeping day clamped to month length.
    
    Args:
        base_date: The starting date.
        delta: Number of months to shift (positive for future, negative for past).
    
    Returns:
        date: The shifted date with day clamped to valid range for target month.
    """
    y, m = base_date.year, base_date.month
    new_m_index = (m - 1) + delta
    new_y = y + new_m_index // 12
    new_m = (new_m_index % 12) + 1
    last_day = calendar.monthrange(new_y, new_m)[1]
    return date(new_y, new_m, min(base_date.day, last_day))

@observe
def month_bounds(base_date: date, month_offset: int):
    """Return first and last date of the month after applying offset.
    
    Args:
        base_date: The reference date.
        month_offset: Number of months to offset from base_date.
    
    Returns:
        tuple: (start_date, end_date) representing first and last day of target month.
    """
    start = shift_month(base_date.replace(day=1), month_offset)
    last_day = calendar.monthrange(start.year, start.month)[1]
    end = date(start.year, start.month, last_day)
    return start, end

@observe
def month_weeks(start: date):
    """Build calendar weeks for a month starting at the given date.
    
    Args:
        start: First day of the month (should be day=1).
    
    Returns:
        list: List of weeks, each week is a list of 7 date objects (Monday-Sunday).
              Includes dates from adjacent months to complete partial weeks.
    """
    weeks = []
    cal = calendar.Calendar(firstweekday=0)  
    for week in cal.monthdatescalendar(start.year, start.month):
        weeks.append(list(week))
    return weeks

@observe
def weekly_planner_page():
    """Render the meal planner page.
    """
    st.set_page_config(
        page_title='SmartBites | Meal Planner',
        page_icon='https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/calendar-week.svg',
        layout='wide',
        initial_sidebar_state='collapsed'
    )
    st.title("My Weekly Plan")

    auth = st.session_state.auth
    user_id = st.session_state.get('user_id', None) or auth.get_user_id()

    if "auth" not in st.session_state:
        st.session_state.auth = AuthService()

    if not user_id:
        st.warning("User not logged in properly.")
        st.stop()
    
    user_id = st.session_state.user_id

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

    st.markdown("")

    today = datetime.today().date()
    # Navigation row
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
        recipes = fetch_user_recipes(user_id, start_week, start_week + timedelta(days=6))

        st.markdown(f"### Week {start_week.isocalendar()[1]} ")
        st.markdown("")

        cols = st.columns(7)
        for i, day in enumerate(week_days):
            is_today = (day == today)
            with cols[i]:
                header_bg = "#a5c4a8ab" if is_today else "transparent"
                st.markdown(
                    f"<div style='text-align: center; font-weight: bold; background:{header_bg}; border-radius:6px; padding:4px;'>"
                    f"{day.strftime('%a %d')}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("")
                day_recipes = [r for r in recipes if r["date"] == day]
                if not day_recipes:
                    st.caption("No meals planned")
                for r in day_recipes:
                    if st.button(r["title"], key=f"btn-{day}-{r['title']}", use_container_width=True):
                        st.session_state.selected_recipe = r
                        st.session_state.dialog_open = False
                        st.rerun()

    else:
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
        recipes = fetch_user_recipes(user_id, month_start, month_end)
        st.markdown(f"### {month_start.strftime('%B %Y')} ")

        weeks = month_weeks(month_start)
        for week in weeks:
            row_cols = st.columns(7)
            for col, day in zip(row_cols, week):
                in_month = (day.month == month_start.month)
                is_today = (day == today)
                with col:
                    header_bg = "#a5c4a8ab" if is_today else "transparent"
                    st.markdown(
                                f"<div style='text-align: center; font-weight: bold; background:{header_bg}; border-radius:6px; padding:4px;'>"
                                f"{day.strftime('%a %d')}</div>",
                                unsafe_allow_html=True,
                    )
                    st.markdown("")
                    
                    if in_month:
                        day_recipes = [r for r in recipes if r["date"] == day]
                        if not day_recipes:
                            st.caption("No meals")
                        for r in day_recipes:
                            if st.button(r["title"], key=f"m-{day}-{r['title']}", use_container_width=True):
                                st.session_state.selected_recipe = r
                                st.session_state.dialog_open = False
                                st.rerun()

    # Recipe pop-up
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
                    ingredient_lines = ingredients.split(',')
                    for ingredient in ingredient_lines:
                        ingredient = ingredient.strip()
                        if ingredient:
                            st.markdown(f"• {ingredient}")
                elif isinstance(ingredients, list):
                    for ingredient in ingredients:
                        st.markdown(f"• {ingredient}")

            # Parse and display instructions as numbered steps
            st.markdown(f"**Instructions:**")
            instructions = recipe['details']
            
            steps = re.split(r'\d+\.\s+', instructions)
            steps = [step.strip() for step in steps if step.strip()]
            
            for i, step in enumerate(steps, 1):
                st.markdown(f"• **Step {i}:** {step}")
            
            if recipe.get('link'):
                st.markdown(f"**[View Recipe Link]({recipe['link']})**")

        show_event_dialog()
        