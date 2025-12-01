import unittest
from types import SimpleNamespace

from src.services.receipt_service import ReceiptService
from src.services.recipe_service import RecipeService
from src.services.mealplan_service import MealPlanService


class MockAdapterBasic:
    def __init__(self, with_table=False, rows=None):
        self._has_table = with_table
        self._data = rows or []
        self.client = SimpleNamespace()

        def table(name):
            class Table:
                def __init__(self, data):
                    self._data = data

                def select(self, *args, **kwargs):
                    return self

                def eq(self, *a, **k):
                    return self

                def limit(self, n):
                    return self

                def insert(self, payload):
                    class Inserter:
                        def __init__(self, data, payload):
                            self.data = data
                            self.payload = payload

                        def execute(self):
                            # simulate inserted row
                            return SimpleNamespace(data=[{**self.payload, 'id': 'mock-row'}])

                    return Inserter(self._data, payload)

                def execute(self):
                    return SimpleNamespace(data=self._data)

            return Table(self._data)

        self.client.table = table

    def insert_receipt(self, user_id, data):
        row = {'id': 'r-mock', 'user_id': user_id, 'payload': data}
        self._data.append(row)
        return row

    def upsert_pantry_item(self, *a, **k):
        return {'ok': True}

    def remove_shopping_list_item_if_present(self, *a, **k):
        return None


class TestServiceStandardization(unittest.TestCase):
    def test_receipt_service_adapter_injection(self):
        mock = MockAdapterBasic()
        svc = ReceiptService(adapter=mock)
        self.assertIs(svc.adapter, mock)

    def test_recipe_service_get_saved_recipes_with_adapter(self):
        mock = MockAdapterBasic(with_table=True, rows=[{'id': 'r1'}])
        svc = RecipeService(adapter=mock)
        res = svc.get_saved_recipes('user-xyz')
        self.assertIsInstance(res, list)

    def test_mealplan_save_plan_fallback_and_db(self):
        # When adapter has no table, returns payload
        mock_no_db = MockAdapterBasic(with_table=False)
        msvc = MealPlanService(adapter=mock_no_db)
        payload = msvc.save_plan('u1', '2025-12-01', '2025-12-07', [{'slot': 1}])
        self.assertIsInstance(payload, dict)

        # With DB adapter, returns inserted row
        mock_db = MockAdapterBasic(with_table=True)
        msvc2 = MealPlanService(adapter=mock_db)
        row = msvc2.save_plan('u1', '2025-12-01', '2025-12-07', [{'slot': 1}])
        self.assertIsInstance(row, dict)
        self.assertEqual(row.get('id'), 'mock-row')


if __name__ == '__main__':
    unittest.main()
