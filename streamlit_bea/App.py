import sys
from pathlib import Path
import json
import uuid

# Ensure project root is on sys.path so `src` package is importable when running Streamlit
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
from types import SimpleNamespace
from src.utils.text_normalization import normalize_text


st.set_page_config(page_title='SmartBites - Bea Demo')

st.title('SmartBites — Mini Demo (Bea)')


class MockAdapter:
    """Lightweight in-memory adapter used by the demo when no Supabase is present.

    Data is stored in `st.session_state['demo_pantry']` so it survives reruns.
    """

    def __init__(self):
        if 'demo_pantry' not in st.session_state:
            st.session_state['demo_pantry'] = []
        self._data = st.session_state['demo_pantry']
        # simple client mock for PantryService.list_items
        def table(name):
            class Table:
                def select(self, *args, **kwargs):
                    return self

                def eq(self, *a, **k):
                    return self

                def limit(self, n):
                    return self

                def delete(self):
                    return self

                def update(self, doc):
                    # no-op for demo; updates handled on the adapter methods
                    return self

                def insert(self, payload):
                    return self

                def execute(self):
                    return SimpleNamespace(data=self._data)

            return Table()

        self.client = SimpleNamespace(table=table)

    def upsert_pantry_item(self, user_id, name, normalized_name, quantity, unit, source_receipt_id=None):
        # try to find existing
        for row in self._data:
            if row.get('user_id') == user_id and row.get('normalized_name') == normalized_name:
                # aggregate
                try:
                    row['quantity'] = (row.get('quantity') or 0) + (quantity or 0)
                except Exception:
                    row['quantity'] = quantity
                row['unit'] = unit or row.get('unit')
                return row

        new_row = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'name': name,
            'normalized_name': normalized_name,
            'quantity': quantity,
            'unit': unit,
            'source_receipt_id': source_receipt_id,
        }
        self._data.append(new_row)
        return new_row

    def delete_pantry_item(self, item_id):
        before = list(self._data)
        self._data[:] = [r for r in self._data if r.get('id') != item_id]
        return len(before) != len(self._data)


def safe_import(path: str, attr: str):
    try:
        module = __import__(path, fromlist=[attr])
        return getattr(module, attr)
    except Exception:
        return None


# Try to load real services; if unavailable, we'll provide local mocks.
PantryService = safe_import('src.services.pantry_service', 'PantryService')
ShoppingListService = safe_import('src.services.shopping_list_service', 'ShoppingListService')
MealPlanService = safe_import('src.services.mealplan_service', 'MealPlanService')
RecipeService = safe_import('src.services.recipe_service', 'RecipeService')
ReceiptService = safe_import('src.services.receipt_service', 'ReceiptService')


class MockPantryService:
    def __init__(self):
        self.adapter = MockAdapter()

    def list_items(self, user_id: str):
        return list(self.adapter._data)

    def add_or_update_item(self, user_id: str, name: str, quantity: float = None, unit: str = None, source_receipt_id: str = None):
        norm = normalize_text(name)
        return self.adapter.upsert_pantry_item(user_id, name, norm, quantity, unit, source_receipt_id=source_receipt_id)


class MockShoppingListService:
    def __init__(self):
        if 'demo_shopping' not in st.session_state:
            st.session_state['demo_shopping'] = []
        self._data = st.session_state['demo_shopping']

    def list_items(self, user_id: str):
        return [r for r in self._data if r.get('user_id') == user_id]

    def add_item(self, user_id: str, name: str, quantity=None, unit=None, section=None, auto_added_by=None):
        row = {'id': str(uuid.uuid4()), 'user_id': user_id, 'name': name, 'quantity': quantity, 'unit': unit, 'section': section}
        self._data.append(row)
        return row

    def remove_item(self, user_id: str, item_id: str):
        before = list(self._data)
        self._data[:] = [r for r in self._data if not (r.get('id') == item_id and r.get('user_id') == user_id)]
        return len(before) != len(self._data)


class MockMealPlanService:
    def __init__(self):
        pass

    def propose_plan(self, ingredients, preferences):
        # very small wrapper around X_meal_planner if available
        m = safe_import('src.services.X_meal_planner', 'generate_meal_plan')
        if m:
            return m(ingredients, preferences)
        # fallback: create simple 3-day dinner-only plan using pantry ingredients
        plan = []
        days = ['Monday', 'Tuesday', 'Wednesday']
        for d in days:
            plan.append({'day': d, 'meals': [{'slot': 'Dinner', 'recipe': ingredients[0] if ingredients else 'Simple Meal', 'missing_ingredients': []}]})
        return plan

    def get_schedule_and_shopping(self, plan):
        s = safe_import('src.services.X_meal_planner', 'schedule_meals')
        if s:
            return s(plan)
        # simple aggregation
        schedule = {d['day']: {m['slot']: m['recipe'] for m in d['meals']} for d in plan}
        missing = sorted({ing for d in plan for m in d['meals'] for ing in m.get('missing_ingredients', [])})
        return {'schedule': schedule, 'aggregated_shopping_list': missing}


class MockRecipeService:
    def __init__(self):
        pass

    def search_by_ingredients(self, ingredients, strict=True):
        # local quick match
        m = safe_import('src.services.X_meal_planner', 'match_ingredients_to_recipes')
        if m:
            return m(ingredients)
        return [{'name': 'Simple Stir Fry', 'ingredients': ingredients, 'match_score': 1.0, 'missing_ingredients': []}]


class MockReceiptService:
    def __init__(self):
        pass

    def analyze_receipt(self, file_bytes: bytes, mime_type: str = 'application/pdf'):
        # return a tiny mocked receipt
        return {
            'store_name': 'Demo Store',
            'purchase_date': '2025-11-29',
            'items': [
                {'name': 'Milk', 'quantity': 1, 'unit': 'L', 'unit_price': 1.5},
                {'name': 'Eggs', 'quantity': 12, 'unit': 'pcs', 'unit_price': 2.5},
            ],
            'total': 4.0,
        }

    def process_and_store_receipt(self, file_bytes: bytes, mime_type: str, user_id: str):
        data = self.analyze_receipt(file_bytes, mime_type)
        # best-effort: add items to demo pantry if available
        p = svc
        for item in data.get('items', []):
            try:
                p.add_or_update_item(user_id, item.get('name'), item.get('quantity') or 1, item.get('unit'))
            except Exception:
                pass
        return data


# Instantiate services later according to a demo setting (safe default: mocks)
st.sidebar.header('Demo Settings')
use_live = st.sidebar.checkbox('Connect to Supabase (live DB)', value=False, help='When enabled the demo will attempt to use configured Supabase services; leave off to use safe local mocks.')

if use_live:
    svc = PantryService() if PantryService else MockPantryService()
    shopping_svc = ShoppingListService() if ShoppingListService else MockShoppingListService()
    mealplan_svc = MealPlanService() if MealPlanService else MockMealPlanService()
    recipe_svc = RecipeService() if RecipeService else MockRecipeService()
    receipt_svc = ReceiptService() if ReceiptService else MockReceiptService()
else:
    svc = MockPantryService()
    shopping_svc = MockShoppingListService()
    mealplan_svc = MockMealPlanService()
    recipe_svc = MockRecipeService()
    receipt_svc = MockReceiptService()


# --- UI: Sidebar navigation ---
page = st.sidebar.selectbox('Page', ['Login', 'Pantry', 'Shopping List', 'Meal Planner', 'Receipts', 'Recipes', 'Chatbot', 'Profile'])


def render_pantry():
    st.header('Pantry')
    with st.expander('Add item (manual)'):
        with st.form('add_item'):
            name = st.text_input('Item name', '')
            qty = st.number_input('Quantity', min_value=0.0, value=1.0, step=0.5)
            unit = st.text_input('Unit', value='pcs')
            submitted = st.form_submit_button('Add')
            if submitted:
                if not name.strip():
                    st.warning('Enter an item name')
                else:
                    item = svc.add_or_update_item('demo-user', name.strip(), float(qty), unit.strip() or None)
                    st.success(f"Added/updated: {item.get('name')} ({item.get('quantity')} {item.get('unit')})")

    st.subheader('Items')
    items = svc.list_items('demo-user')
    if not items:
        st.info('No pantry items yet — add some above.')
    else:
        for row in items:
            cols = st.columns([4, 1, 1, 1])
            with cols[0]:
                st.markdown(f"**{row.get('name')}** — {row.get('quantity')} {row.get('unit')}")
            with cols[1]:
                if st.button('Remove', key=f"remove-{row.get('id')}"):
                    deleted = False
                    if hasattr(svc.adapter, 'delete_pantry_item'):
                        deleted = svc.adapter.delete_pantry_item(row.get('id'))
                    else:
                        try:
                            svc.adapter._data[:] = [r for r in svc.adapter._data if r.get('id') != row.get('id')]
                            deleted = True
                        except Exception:
                            deleted = False
                    if deleted:
                        st.experimental_rerun()
            with cols[2]:
                if st.button('Inc', key=f"inc-{row.get('id')}"):
                    try:
                        norm = normalize_text(row.get('name'))
                        svc.adapter.upsert_pantry_item('demo-user', row.get('name'), norm, 1, row.get('unit'))
                        st.experimental_rerun()
                    except Exception:
                        st.error('Unable to increment item')
            with cols[3]:
                if st.button('Dec', key=f"dec-{row.get('id')}"):
                    try:
                        current = row.get('quantity') or 0
                        new_qty = (current or 0) - 1
                        if new_qty <= 0:
                            svc.adapter.delete_pantry_item(row.get('id'))
                        else:
                            row['quantity'] = new_qty
                        st.experimental_rerun()
                    except Exception:
                        st.error('Unable to decrement item')


def render_shopping_list():
    st.header('Shopping List')
    with st.form('add_shop'):
        name = st.text_input('Item name')
        qty = st.number_input('Quantity', min_value=0.0, value=1.0)
        unit = st.text_input('Unit', value='pcs')
        submitted = st.form_submit_button('Add')
        if submitted:
            shopping_svc.add_item('demo-user', name, qty, unit)
            st.success('Added to shopping list')

    items = shopping_svc.list_items('demo-user')
    if not items:
        st.info('Shopping list is empty')
    else:
        for it in items:
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(f"{it.get('name')} — {it.get('quantity')} {it.get('unit')}")
            with cols[1]:
                if st.button('Remove', key=f"shop-remove-{it.get('id')}"):
                    shopping_svc.remove_item('demo-user', it.get('id'))
                    st.experimental_rerun()


def render_meal_planner():
    st.header('Meal Planner')
    st.write('Generate a simple meal plan based on pantry contents')
    days = st.number_input('Days', min_value=1, max_value=7, value=3)
    meals_per_day = st.selectbox('Meals per day', [1, 2, 3], index=0)
    diet = st.text_input('Diet (comma-separated tags)', '')
    if st.button('Generate Plan'):
        # build pantry snapshot
        user = st.session_state.get('user_id', 'demo-user')
        pantry_items = [i.get('normalized_name') or normalize_text(i.get('name')) for i in svc.list_items(user)]
        prefs = {'days': days, 'meals_per_day': meals_per_day, 'diet': [d.strip() for d in diet.split(',') if d.strip()], 'days_count': days}
        plan = mealplan_svc.propose_plan(pantry_items, prefs)
        # normalize plan into a session-storable structure
        st.session_state['current_plan'] = plan

    plan = st.session_state.get('current_plan')
    if not plan:
        st.info('No plan generated yet — use Generate Plan.')
        return

    # Render a calendar-like table with 2 slots per day (Slot A / Slot B)
    st.subheader('Calendar View')
    days_list = [d.get('day', f'Day {i+1}') for i, d in enumerate(plan)]
    cols = st.columns(len(days_list))
    # Header row
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**{days_list[i]}**")

    # Two slot rows
    for slot_index in range(2):
        cols = st.columns(len(days_list))
        for i, col in enumerate(cols):
            day_entry = plan[i]
            meals = day_entry.get('meals', [])
            # pick meal for this slot index if available
            meal = meals[slot_index] if slot_index < len(meals) else {'recipe': '—', 'missing_ingredients': []}
            with col:
                st.write(f"**Slot {slot_index+1}**")
                st.write(meal.get('recipe'))
                if meal.get('missing_ingredients'):
                    st.caption('Missing: ' + ', '.join(meal.get('missing_ingredients')))
                # allow edit
                edit_key = f'edit-{i}-{slot_index}'
                if st.button('Edit', key=edit_key):
                    st.session_state[f'editing-{i}-{slot_index}'] = True
                if st.session_state.get(f'editing-{i}-{slot_index}'):
                    new_name = st.text_input(f'New recipe for {days_list[i]} slot {slot_index+1}', value=meal.get('recipe') or '', key=f'input-{i}-{slot_index}')
                    if st.button('Save', key=f'save-{i}-{slot_index}'):
                        # patch into session plan
                        plan[i]['meals'][slot_index]['recipe'] = new_name
                        st.session_state['current_plan'] = plan
                        st.session_state[f'editing-{i}-{slot_index}'] = False
                        st.experimental_rerun()

    # Show aggregated shopping list
    scheduled = mealplan_svc.get_schedule_and_shopping(plan)
    st.subheader('Aggregated shopping list')
    st.write(scheduled.get('aggregated_shopping_list', []))


def render_receipts():
    st.header('Receipts (demo)')
    st.write('Upload a receipt image/PDF and run a mocked analysis (or real if configured).')
    uploaded = st.file_uploader('Receipt file', type=['pdf', 'png', 'jpg', 'jpeg'])
    if uploaded is not None:
        try:
            data = receipt_svc.process_and_store_receipt(uploaded.read(), uploaded.type, 'demo-user')
            st.success('Processed receipt (demo)')
            st.json(data)
        except Exception as e:
            st.error(f'Failed to process receipt: {e}')


def render_login():
    st.header('Login')
    if 'user_id' in st.session_state:
        st.success(f"Logged in as: {st.session_state.get('user_id')}")
        if st.button('Log out'):
            for k in list(st.session_state.keys()):
                # preserve demo state keys except profile/history
                if k.startswith('demo_') or k.startswith('profile'):
                    continue
                del st.session_state[k]
            st.experimental_rerun()
        return

    st.write('Choose demo login or provide a user id for live mode.')
    with st.form('login_form'):
        demo = st.checkbox('Use demo user', value=True)
        user_input = st.text_input('User id (UUID) — for live mode only', '')
        submitted = st.form_submit_button('Log in')
        if submitted:
            if demo:
                st.session_state['user_id'] = 'demo-user'
                # seed a demo profile
                st.session_state['profile'] = {'id': 'demo-user', 'username': 'demo', 'full_name': 'Demo User', 'diet_type': 'balanced', 'allergies': []}
                st.success('Logged in as demo-user')
            else:
                if not user_input.strip():
                    st.error('Enter a user id for live mode')
                else:
                    st.session_state['user_id'] = user_input.strip()
                    # attempt to fetch profile from DB
                    try:
                        user_id = st.session_state['user_id']
                        resp = None
                        if hasattr(svc, 'adapter') and getattr(svc.adapter, 'client', None):
                            resp = svc.adapter.client.table('users').select('*').eq('id', user_id).execute()
                        if resp and getattr(resp, 'data', None):
                            st.session_state['profile'] = resp.data[0]
                            st.success('Logged in (live)')
                        else:
                            st.session_state['profile'] = {'id': user_id, 'username': user_id, 'full_name': '', 'diet_type': '', 'allergies': []}
                            st.info('Logged in but no profile found locally — you can edit it in Profile page')
                    except Exception as e:
                        st.error(f'Login failed: {e}')


def render_recipes():
    st.header('Recipe Library')
    st.write('Search recipes by pantry ingredients (demo).')
    ings = st.text_input('Ingredients (comma-separated)')
    strict = st.checkbox('Strict (only recipes with no missing ingredients)', value=True)
    if st.button('Search'):
        ingredients = [i.strip() for i in ings.split(',') if i.strip()]
        results = recipe_svc.search_by_ingredients(ingredients, strict=strict)
        st.write(results)


def render_chatbot():
    st.header('Chatbot (demo)')
    st.write('Ask simple questions about receipts or pantry. Uses mocked AI if not configured.')

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    # Display history above
    for msg in st.session_state['chat_history']:
        role = msg.get('role', 'user')
        text = msg.get('text', '')
        if role == 'user':
            st.markdown(f"**You:** {text}")
        else:
            st.markdown(f"**Assistant:** {text}")

    # Input
    question = st.text_input('Your question', key='chat_input')
    if st.button('Send'):
        if not question.strip():
            st.warning('Enter a question')
        else:
            # append user message
            st.session_state['chat_history'].append({'role': 'user', 'text': question})
            # create context from last receipt or pantry snapshot
            ctx = st.session_state.get('last_receipt', {}) or {'pantry': svc.list_items(st.session_state.get('user_id', 'demo-user'))}
            try:
                if hasattr(receipt_svc, 'answer_question'):
                    ans = receipt_svc.answer_question(question, ctx)
                else:
                    ans = 'Demo assistant: I can answer simple receipt and pantry questions in this demo.'
            except Exception as e:
                ans = f'Error from assistant: {e}'
            st.session_state['chat_history'].append({'role': 'assistant', 'text': ans})
            # clear input
            st.session_state['chat_input'] = ''
            st.experimental_rerun()


def render_profile():
    st.header('Profile')
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.info('Not logged in. Use the Login page to sign in.')
        return

    # Attempt to fetch live profile when use_live is on
    if use_live and hasattr(svc, 'adapter') and getattr(svc.adapter, 'client', None):
        try:
            resp = svc.adapter.client.table('users').select('*').eq('id', user_id).execute()
            profile = resp.data[0] if getattr(resp, 'data', None) else st.session_state.get('profile', {})
        except Exception:
            profile = st.session_state.get('profile', {})
    else:
        profile = st.session_state.get('profile', {})

    if not profile:
        profile = {'id': user_id, 'username': '', 'full_name': '', 'diet_type': '', 'allergies': ''}

    profile['full_name'] = st.text_input('Full name', profile.get('full_name', ''))
    profile['diet_type'] = st.text_input('Diet type', profile.get('diet_type', ''))
    profile['allergies'] = st.text_input('Allergies (comma-separated)', ','.join(profile.get('allergies', []) if isinstance(profile.get('allergies', []), list) else [profile.get('allergies', '')]))

    if st.button('Save Profile'):
        # Save to session and attempt DB save when live
        st.session_state['profile'] = profile
        if use_live and hasattr(svc, 'adapter') and getattr(svc.adapter, 'client', None):
            try:
                payload = dict(profile)
                payload['id'] = user_id
                svc.adapter.client.table('users').upsert(payload).execute()
                st.success('Profile saved to DB')
            except Exception as e:
                st.warning(f'Profile saved locally, DB save failed: {e}')
        else:
            st.success('Profile saved (session only)')


PAGE_RENDERERS = {
    'Pantry': render_pantry,
    'Shopping List': render_shopping_list,
    'Meal Planner': render_meal_planner,
    'Receipts': render_receipts,
    'Recipes': render_recipes,
    'Chatbot': render_chatbot,
    'Profile': render_profile,
}


PAGE_RENDERERS.get(page, render_pantry)()


st.markdown('---')
st.caption('This demo implements core flows from NOTES.md: Pantry, Shopping List, Meal Planning, Receipts, Recipes, Chatbot and Profile. It uses lightweight mocks when external services are not configured.')
