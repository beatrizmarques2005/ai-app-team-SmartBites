"""
Meal Plan Flow Module
---------------------

This module handles the meal plan flow within the chat application. It processes user inputs related to meal planning,
including approvals and edits to the meal plan.

"""

from langfuse import observe

@observe()
def handle_meal_plan_flow(chat, user_input: str):
    """
    Process user input for meal plan approval and modification flow.
    This function handles the conversational logic for managing a pending meal plan,
    including approval, saving, and changing individual meals.
    Args:
        chat: The chat object containing the pending meal plan state.
        user_input (str): The user's input text to be processed.
    Returns:
        str or None: A response message to the user if an action is triggered,
                     or None if no specific flow action applies.
    Flow:
        - If the meal plan is awaiting approval and user says "approve" or "save",
          clears the plan and returns a confirmation message.
        - If the meal plan is awaiting approval, prompts user to approve or change.
        - If the plan has meals and user says "change", prompts which meal to change.
        - Otherwise, returns None.
    """
    plan = chat.pending_meal_plan
    text = user_input.lower()

    if plan.awaiting_approval:
        if "approve" in text or "save" in text:
            plan.clear()
            return " Meal plan approved and saved!"

        return "Would you like to approve the meal plan or change a meal?"

    if plan.meals and "change" in text:
        return "Sure — which meal would you like to change?"

    return None
