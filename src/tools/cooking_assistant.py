"""
Cooking Assistant Module
------------------------

Provides cooking advice based on food type, cooking method, and desired outcome.

"""
from langfuse import observe

class CookingAssistant:

    @observe
    def advise(
    self,
    food: str,
    method: str,
    goal: str,
    thickness_cm: float | None = None,
    weight_g: float | None = None,
    heat: str = "medium",
    state: dict | None = None
    ) -> dict:
        
        """
        Provide cooking advice based on food type, cooking method, and desired outcome.
        Validates required parameters and normalizes input values. Returns a dictionary
        containing the normalized parameters and any missing required fields.
        Args:
            food (str): The type of food to cook.
            method (str): The cooking method to use (e.g., 'fry', 'bake', 'boil').
            goal (str): The desired cooking outcome (e.g., 'crispy', 'tender', 'golden').
            thickness_cm (float | None, optional): Thickness of the food in centimeters. Defaults to None.
            weight_g (float | None, optional): Weight of the food in grams. Defaults to None.
            heat (str, optional): Heat level for cooking. Defaults to "medium".
            state (dict | None, optional): Additional state information about the cooking process. Defaults to None.
        Returns:
            dict: A dictionary containing:
                - food (str | None): Normalized food name (lowercase).
                - method (str | None): Normalized cooking method (lowercase).
                - goal (str | None): Normalized cooking goal (lowercase).
                - thickness_cm (float | None): Food thickness if provided.
                - weight_g (float | None): Food weight if provided.
                - heat (str): Heat level setting.
                - state (dict): Cooking state information (empty dict if not provided).
                - missing (list): List of missing required parameters.
        """
        
        missing = []

        if not food:
            missing.append("food")
        if not method:
            missing.append("method")
        if not goal:
            missing.append("goal")
        return {
            "food": food.lower() if food else None,
            "method": method.lower() if method else None,
            "goal": goal.lower() if goal else None,
            "thickness_cm": thickness_cm,
            "weight_g": weight_g,
            "heat": heat,
            "state": state or {},
            "missing": missing
        }