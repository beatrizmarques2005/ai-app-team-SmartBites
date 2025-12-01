import unittest
from types import SimpleNamespace

from src.services.shopping_list_service import ShoppingListService
from src.services.ingredient_service import IngredientService


class MockAdapterSimple:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self._data = []
        self.client = SimpleNamespace()

        def table(name):
            class Table:
                def __init__(self, parent):
                    self.parent = parent

                def select(self, *args, **kwargs):
                    return self

                def eq(self, *a, **k):
                    return self

                def limit(self, n):
                    return self

                def insert(self, payload):
                    class Inserter:
                        def __init__(self, parent, payload):
                            self.parent = parent
                            self.payload = payload

                        def execute(self):
                            self.parent._data.append(self.payload)
                            return SimpleNamespace(data=[{**self.payload, 'id': 'mock-1'}])

                    return Inserter(self.parent, payload)

                def delete(self):
                    class Deleter:
                        def __init__(self):
                            pass

                        def eq(self, *a, **k):
                            return self

                        def execute(self):
                            return SimpleNamespace(status_code=204)

                    return Deleter()

                def execute(self):
                    return SimpleNamespace(data=self.parent._data)

            if self.should_fail:
                raise Exception("DB unavailable")
            return Table(self)

        self.client.table = table


class MockInventory:
    def __init__(self, items):
        self._items = items

    def get_ingredients_for_recipe(self):
        return self._items


class MockAI:
    def ask_recipe_question(self, recipe, question):
        # return JSON string list
        return '["alt1","alt2"]'


class TestShoppingAndIngredient(unittest.TestCase):
    def test_shopping_list_with_adapter(self):
        mock = MockAdapterSimple()
        svc = ShoppingListService(adapter=mock)

        added = svc.add_item('u1', 'Bananas', 6, 'pcs')
        self.assertIsInstance(added, dict)
        self.assertEqual(added.get('id'), 'mock-1')

        listed = svc.list_items('u1')
        self.assertIsInstance(listed, list)

        removed = svc.remove_item('u1', 'mock-1')
        self.assertTrue(removed)

    def test_shopping_list_db_failure(self):
        mock_fail = MockAdapterSimple(should_fail=True)
        svc = ShoppingListService(adapter=mock_fail)
        self.assertEqual(svc.list_items('u1'), [])
        self.assertEqual(svc.add_item('u1', 'X', 1), {})
        self.assertFalse(svc.remove_item('u1', 'nope'))

    def test_ingredient_service(self):
        inv = MockInventory(['milk', 'egg'])
        ai = MockAI()
        svc = IngredientService(inv, ai)

        recipe = {'ingredients': ['milk', 'flour', 'egg']}
        missing = svc.check_missing(recipe)
        self.assertIn('flour', missing)

        replacements = svc.suggest_replacement('butter')
        self.assertIsInstance(replacements, list)


if __name__ == '__main__':
    unittest.main()
