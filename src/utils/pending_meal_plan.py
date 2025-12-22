"""
PendingMealPlan Module
----------------------

Data structure to hold the state of a pending meal plan.

"""

from langfuse import observe

class PendingMealPlan:
    def __init__(self):
        self.meals = []
        self.missing_items = []
        self.awaiting_approval = False
        self.awaiting_shopping_ok = False
    @observe()
    def clear(self):
        self.__init__()
