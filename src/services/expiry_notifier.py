from inventory import InventoryTool
from datetime import datetime, timedelta
from langfuse import observe

class ExpiryNotifier:
    """Service to warn about soon-to-expire items."""

    def __init__(self, inventory_manager: InventoryTool, warning_days: int=3):
        self.inventory_manager = inventory_manager
        self.warning_days = warning_days

    @observe()
    def expiring_soon(self) -> list[dict]:
        notif = []
        items_status = self.inventory_manager.expiry_check()
        for name, data in items_status.items():
            if 0 < data["days_remaining"] <= self.warning_days:
                notif.append({**data, "item_name": name})
        return notif