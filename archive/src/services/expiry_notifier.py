from langfuse import observe
from .pantry_service import PantryService


class ExpiryNotifier:
    """Service to warn about soon-to-expire items.

    This notifier relies on `PantryService.expiry_check(user_id)` and returns
    items with days_remaining within the configured warning window.
    """

    def __init__(self, pantry_manager: PantryService, warning_days: int = 3):
        self.pantry_manager = pantry_manager
        self.warning_days = warning_days

    @observe()
    def expiring_soon(self, user_id: str) -> list[dict]:
        notif = []
        items_status = self.pantry_manager.expiry_check(user_id)
        for name, data in items_status.items():
            if 0 < data.get("days_remaining", 0) <= self.warning_days:
                notif.append({**data, "item_name": name})
        return notif
