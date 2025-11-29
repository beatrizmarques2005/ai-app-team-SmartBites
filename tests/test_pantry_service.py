import unittest
from types import SimpleNamespace

from src.services.pantry_service import PantryService


class MockAdapter:
    def __init__(self):
        self._data = []
        # simple client mock for list_items
        self.client = SimpleNamespace()
        def table(name):
            class Table:
                def select(self, *args, **kwargs):
                    return self
                def eq(self, *a, **k):
                    return self
                def limit(self, n):
                    return self
                def execute(self):
                    return SimpleNamespace(data=self._data)
            return Table()
        self.client.table = table

    def upsert_pantry_item(self, user_id, name, normalized_name, quantity, unit, source_receipt_id=None):
        row = {
            'id': 'mock-id',
            'user_id': user_id,
            'name': name,
            'normalized_name': normalized_name,
            'quantity': quantity,
            'unit': unit,
            'source_receipt_id': source_receipt_id
        }
        self._data.append(row)
        return row


class TestPantryService(unittest.TestCase):
    def test_add_or_update_item(self):
        svc = PantryService()
        # replace adapter with mock
        mock = MockAdapter()
        svc.adapter = mock

        item = svc.add_or_update_item('user-1', 'Milk', 1, 'L')
        self.assertIsInstance(item, dict)
        self.assertEqual(item['name'], 'Milk')
        # list_items should return stored data
        listed = svc.list_items('user-1')
        self.assertIsInstance(listed, list)


if __name__ == '__main__':
    unittest.main()
