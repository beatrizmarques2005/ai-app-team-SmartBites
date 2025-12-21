import streamlit as st
from datetime import datetime, timedelta
from collections import defaultdict
from src.db.client import supabase
import ast

# --- Helper function ---
def start_of_week(date):
    return date - timedelta(days=date.weekday())


def weekly_planner_page():
    st.set_page_config(page_title="Weekly Planner", page_icon="📆", layout="wide")
    st.title("My Weekly Plan")

    # ---------- Session state ----------
    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0
    if "selected_recipe" not in st.session_state:
        st.session_state.selected_recipe = None
    if "date_search" not in st.session_state:
        st.session_state.date_search = None

    # ---------- Week navigation ----------
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("**<**", type="tertiary"):
        st.session_state.week_offset -= 1
        st.session_state.selected_recipe = None
    if col2.button("Current"):
        st.session_state.week_offset = 0
        st.session_state.selected_recipe = None
    if col3.button("**>**", type="tertiary"):
        st.session_state.week_offset += 1
        st.session_state.selected_recipe = None
    with col4:
        selected_date = st.date_input(
            "🔎",
            value=st.session_state.date_search or datetime.today().date(),
            key="date_picker",
        )
        if selected_date != st.session_state.date_search:
            st.session_state.date_search = selected_date
            st.session_state.week_offset = (
                start_of_week(selected_date)
                - start_of_week(datetime.today().date())
            ).days // 7
            st.session_state.selected_recipe = None

    # ---------- Compute current week ----------
    today = datetime.today().date()
    start_week = start_of_week(today) + timedelta(weeks=st.session_state.week_offset)
    end_week = start_week + timedelta(days=6)
    week_days = [start_week + timedelta(days=i) for i in range(7)]
    st.subheader(f"Week of {start_week.strftime('%b %d, %Y')}")

    # ---------- Fetch recipes ----------
    response = (
        supabase
        .table("recipes")
        .select("""
            id,
            recipe_name,
            meal_date,
            meal_type,
            ingredients,
            instructions,
            link
        """)
        .gte("meal_date", start_week.isoformat())
        .lte("meal_date", end_week.isoformat())
        .execute()
    )
    recipes = response.data or []

    # ---------- Convert meal_date to date and group ----------
    recipes_by_day_and_type = defaultdict(lambda: defaultdict(list))
    for r in recipes:
        r["meal_date"] = datetime.fromisoformat(r["meal_date"]).date()
        recipes_by_day_and_type[r["meal_date"]][r["meal_type"].lower()].append(r)

    # ---------- Calendar header ----------
    header_cols = st.columns(8)  # first column for labels, 7 for days
    header_cols[0].markdown("**Meal**")
    for i, day in enumerate(week_days):
        header_cols[i + 1].markdown(f"**{day.strftime('%a %d')}**")

    # ---------- Meal-type rows ----------
    meal_labels = ["Breakfast", "Lunch", "Dinner", ""]  # last empty row optional

    for row_label in meal_labels:
        row_cols = st.columns(8)
        # Left label
        if row_label:
            row_cols[0].markdown(f"**{row_label}**")
        else:
            row_cols[0].markdown("")  # empty row

        for i, day in enumerate(week_days):
            col = row_cols[i + 1]

            with col:
                # Get recipes for this cell
                if row_label:
                    day_recipes = recipes_by_day_and_type.get(day, {}).get(row_label.lower(), [])
                else:
                    day_recipes = []

                for r in day_recipes:
                    label = f"{r['recipe_name']}"
                    if st.button(label, key=f"recipe-{r['id']}"):
                        st.session_state.selected_recipe = r

    # ---------- Recipe popup ----------
    if st.session_state.selected_recipe:
        recipe = st.session_state.selected_recipe

        @st.dialog("🍽 Recipe details")
        def show_recipe_dialog():
            st.subheader(recipe["recipe_name"])
            st.markdown(f"**Meal type:** {recipe['meal_type'].capitalize()}")
            st.markdown(f"**Date:** {recipe['meal_date']}")

            st.markdown("### 🧾 Ingredients")
            ingredients = recipe["ingredients"]
            if isinstance(ingredients, str):
                try:
                    ingredients = ast.literal_eval(ingredients)
                except Exception:
                    ingredients = [ingredients]

            if isinstance(ingredients, list):
                for item in ingredients:
                    st.markdown(f"- {item}")
            else:
                st.markdown(ingredients)

            st.markdown("### 👩‍🍳 Instructions")
            st.markdown(recipe["instructions"])

            if recipe.get("link"):
                st.markdown(f"🔗 [Recipe link]({recipe['link']})")

        show_recipe_dialog()
