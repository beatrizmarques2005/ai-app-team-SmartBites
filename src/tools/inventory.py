import datetime
from date_calculator import get_food_status

class InventoryTool:
    def __init__(self):
        self.inventory = {}

    def add_item(self, name, quantity, open_date, shelf_life):
        self.inventory[name] = {"quantity": quantity, "open_date": open_date, "shelf_life": shelf_life}
    
    def expiry_check(self):
        status_dict = {}
        for name, data in self.inventory.items():
            if data["quantity"] <= 0:
                continue
            status = get_food_status(data["open_date"], data["shelf_life"])
            status_dict[name] = {**data, **status}
        return status_dict
    
    def get_ingredients_for_recipe(self, prioritize_expiring=True):
        items = self.expiry_check()
        sorted_items = sorted(
            items.items(),
            key=lambda x: x[1]['days_remaining'] if prioritize_expiring else 0
        )
        return [name for name, data in sorted_items if data["status"] != "Expired" and data["quantity"] > 0]
