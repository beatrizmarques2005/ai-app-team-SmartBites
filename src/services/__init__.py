
# just a template

"""
Services package - Business logic layer

All domain-specific logic lives here.
Services orchestrate AI calls, tools, and business rules.
"""

# from .contract_service import ContractService

from .ai_service import AIService
from .document_service import DocumentService
from .receipt_service import ReceiptService
from .ingredient_service import IngredientService
from .recipe_generator import RecipeGeneratorAI
from .user_service import UserService
# from .recipe_crawler import (  # remote/local crawler
#     # _get_recipe_db,
#     match_ingredients_to_recipes,
#     generate_meal_plan,
# )
from .recipe_scraper import RecipeScraper
from .pantry_service import PantryService
from .shopping_list_service import ShoppingListService
from .recipe_service import RecipeService
from .mealplan_service import MealPlanService

__all__ = [
    'AIService',
    'DocumentService',
    'ReceiptService',
    'IngredientService',
    'UserService',
    'RecipeGeneratorAI',
    'RecipeScraper',
    'PantryService',
    'ShoppingListService',
    'RecipeService',
    'MealPlanService',
    'match_ingredients_to_recipes',
    'generate_meal_plan',
]
