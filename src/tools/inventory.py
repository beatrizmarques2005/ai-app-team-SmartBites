"""
Inventory helper tool

Status: RELEVANT for MVP.
Reason: Provides helper functions for listing and formatting pantry data.
"""


class InventoryTool:
    """Domain tool for managing kitchen inventory."""

    def __init__(self):
        self._inventory = {}

    def add_item(self, name: str, quantity: float, open_date: str, shelf_life: int):
        self._inventory[name.lower()] = {
            "quantity": quantity,
            "open_date": open_date,
            "shelf_life": shelf_life
        }

    def expiry_check(self) -> dict:
        from date_calculator import get_food_status
        status = {}
        for name, data in self._inventory.items():
            if data["quantity"] <= 0:
                continue
            status[name] = {**data, **get_food_status(data["open_date"], data["shelf_life"])}
        return status

    def get_ingredients_for_recipe(self, prioritize_expiring=True) -> list[str]:
        items = self.expiry_check()
        sorted_items = sorted(
            items.items(),
            key=lambda x: x[1]["days_remaining"] if prioritize_expiring else 0
        )
        return [
            name for name, data in sorted_items
            if data["status"] != "Expired" and data["quantity"] > 0
        ]
