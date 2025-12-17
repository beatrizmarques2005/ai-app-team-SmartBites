
# from src.tools.user_checker import UserChecker
# from src.services.ai_service import AIService
# from src.tools.ingredient_checker import IngredientChecker



# def full_user_context():
#     """Aggregate and return a summary of user information and preferences."""
#     identify_user = UserChecker().identify_user()
#     preferences = UserChecker().preferences()
#     available_ingredients = IngredientChecker().available_ingredients()

#     user_context = "User Information:\n"
#     if identify_user:
#         user_context += f"- {identify_user}\n"
#     if preferences:
#         user_context += f"- Preferences: {preferences}\n"
#     if available_ingredients:
#         user_context += f"- Available Ingredients: {available_ingredients}\n"

#     return user_context.strip()
