
class PendingMealPlan:
    def __init__(self):
        self.meals = []
        self.missing_items = []
        self.awaiting_approval = False
        self.awaiting_shopping_ok = False

    def clear(self):
        self.__init__()
