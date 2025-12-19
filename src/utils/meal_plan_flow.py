
def handle_meal_plan_flow(chat, user_input: str):
    plan = chat.pending_meal_plan
    text = user_input.lower()

    # Example: approval
    if plan.awaiting_approval:
        if "approve" in text or "save" in text:
            plan.clear()
            return " Meal plan approved and saved!"

        return "Would you like to approve the meal plan or change a meal?"

    # Example: editing
    if plan.meals and "change" in text:
        return "Sure — which meal would you like to change?"

    # Not actually about meal planning
    return None