import streamlit as st
from streamlit_bea._common import get_services

st.set_page_config(page_title='Meal Plan - SmartBites')
use_live = st.sidebar.checkbox('Use live services (Supabase)', value=False)
services = get_services(use_live=use_live)
svc = services['pantry']
mealplan = services['mealplan']

st.title('Meal Planner')
days = st.number_input('Days', min_value=1, max_value=7, value=3)
meals_per_day = st.selectbox('Meals per day', [1,2,3], index=2)
diet = st.text_input('Diet (comma-separated)')

if st.button('Generate'):
    pantry_items = []
    try:
        pantry_items = [i.get('normalized_name') or i.get('name') for i in svc.list_items('demo-user')]
    except Exception:
        try:
            pantry_items = [i.get('normalized_name') or i.get('name') for i in getattr(svc, 'adapter')._data]
        except Exception:
            pantry_items = []

    prefs = {'days': days, 'meals_per_day': meals_per_day, 'diet': [d.strip() for d in diet.split(',') if d.strip()]}
    plan = mealplan.propose_plan(pantry_items, prefs)
    # ensure plan has expected shape: list of days each with 'meals' list
    st.session_state['current_plan'] = plan

plan = st.session_state.get('current_plan') or []
if not plan:
    st.info('No plan yet — generate one.')
else:
    # render a visual grid: columns = days, rows = meals_per_day (max 3)
    cols = st.columns(len(plan))
    # Header: day names
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**{plan[i].get('day', f'Day {i+1}')}**")

    # Rows for meals
    for meal_row in range(min(3, meals_per_day)):
        cols = st.columns(len(plan))
        for i, col in enumerate(cols):
            with col:
                meals = plan[i].get('meals', [])
                meal = meals[meal_row] if meal_row < len(meals) else {'recipe': '—', 'missing_ingredients': []}
                st.markdown(f"**Meal {meal_row+1}**")
                st.write(meal.get('recipe'))
                if meal.get('missing_ingredients'):
                    st.caption('Missing: ' + ', '.join(meal.get('missing_ingredients')))
                # allow edit inline
                if st.button('Edit', key=f'edit-{i}-{meal_row}'):
                    st.session_state[f'editing-{i}-{meal_row}'] = True
                if st.session_state.get(f'editing-{i}-{meal_row}'):
                    new_name = st.text_input(f'New recipe for {plan[i].get("day", f"Day {i+1}")} meal {meal_row+1}', value=meal.get('recipe') or '', key=f'input-{i}-{meal_row}')
                    if st.button('Save', key=f'save-{i}-{meal_row}'):
                        if 'meals' not in plan[i]:
                            plan[i]['meals'] = []
                        # ensure the meals list is long enough
                        while len(plan[i]['meals']) <= meal_row:
                            plan[i]['meals'].append({'slot': f'Meal {len(plan[i]["meals"]) + 1}', 'recipe': '—', 'missing_ingredients': []})
                        plan[i]['meals'][meal_row]['recipe'] = new_name
                        st.session_state['current_plan'] = plan
                        st.session_state[f'editing-{i}-{meal_row}'] = False
                        st.experimental_rerun()

    # show aggregated shopping list
    scheduled = mealplan.get_schedule_and_shopping(plan)
    st.subheader('Aggregated shopping list')
    st.write(scheduled.get('aggregated_shopping_list', []))
