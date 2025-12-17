class CookingAssistant:

    def advise(
    self,
    food: str,
    method: str,
    goal: str,
    thickness_cm: float | None = None,
    weight_g: float | None = None,
    heat: str = "medium",
    state: dict | None = None
    ):
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