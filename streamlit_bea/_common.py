import sys
from pathlib import Path
from types import SimpleNamespace
import uuid
import streamlit as st

# Ensure project root is on sys.path so `src` package is importable when running Streamlit
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.text_normalization import normalize_text


def safe_import(path: str, attr: str):
    try:
        module = __import__(path, fromlist=[attr])
        return getattr(module, attr)
    except Exception:
        return None


class MockAdapter:
    def __init__(self):
        if 'demo_pantry' not in st.session_state:
            st.session_state['demo_pantry'] = []
        self._data = st.session_state['demo_pantry']

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
                    return self

                def insert(self, payload):
                    return self

                def execute(self):
                    return SimpleNamespace(data=self._data)

            return Table()

        self.client = SimpleNamespace(table=table)

    def upsert_pantry_item(self, user_id, name, normalized_name, quantity, unit, source_receipt_id=None):
        for row in self._data:
            if row.get('user_id') == user_id and row.get('normalized_name') == normalized_name:
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
        # very small fallback
        plan = []
        days = ['Monday', 'Tuesday', 'Wednesday'][: max(1, int(preferences.get('days', 3)))]
        for d in days:
            plan.append({'day': d, 'meals': [{'slot': 'Dinner', 'recipe': ingredients[0] if ingredients else 'Simple Meal', 'missing_ingredients': []}]})
        return plan

    def get_schedule_and_shopping(self, plan):
        schedule = {d['day']: {m['slot']: m['recipe'] for m in d['meals']} for d in plan}
        missing = sorted({ing for d in plan for m in d['meals'] for ing in m.get('missing_ingredients', [])})
        return {'schedule': schedule, 'aggregated_shopping_list': missing}


class MockRecipeService:
    def __init__(self):
        pass

    def search_by_ingredients(self, ingredients, strict=True):
        return [{'name': 'Simple Stir Fry', 'ingredients': ingredients, 'match_score': 1.0, 'missing_ingredients': []}]


class MockReceiptService:
    def __init__(self):
        pass

    def analyze_receipt(self, file_bytes: bytes, mime_type: str = 'application/pdf'):
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
        p = MockPantryService()
        for item in data.get('items', []):
            try:
                p.add_or_update_item(user_id, item.get('name'), item.get('quantity') or 1, item.get('unit'))
            except Exception:
                pass
        return data


def get_services(use_live: bool = False):
    PantryService = safe_import('src.services.pantry_service', 'PantryService')
    ShoppingListService = safe_import('src.services.shopping_list_service', 'ShoppingListService')
    MealPlanService = safe_import('src.services.mealplan_service', 'MealPlanService')
    RecipeService = safe_import('src.services.recipe_service', 'RecipeService')
    ReceiptService = safe_import('src.services.receipt_service', 'ReceiptService')
    UserService = safe_import('src.services.user_service', 'UserService')

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

    return {
        'pantry': svc,
        'shopping': shopping_svc,
        'mealplan': mealplan_svc,
        'recipe': recipe_svc,
        'receipt': receipt_svc,
        'user': UserService() if (use_live and UserService) else None,
    }
