# Nutritional Analyser Tool
# -------------------------
# Purpose: Analyze nutrition of meals.

from collections import defaultdict

# Sample nutrition database (per 100g)
NUTRITION_DB = {
    "chicken breast": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6},
    "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3},
    "broccoli": {"calories": 55, "protein": 3.7, "carbs": 11, "fat": 0.6},
    "olive oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100},
    "tofu": {"calories": 76, "protein": 8, "carbs": 1.9, "fat": 4.8},
    "egg": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11},
    "milk": {"calories": 42, "protein": 3.4, "carbs": 5, "fat": 1},
}

# Sample allergen database
ALLERGEN_DB = {
    "milk": "dairy",
    "egg": "egg",
    "tofu": "soy",
    "peanut": "nuts",
    "almond": "nuts",
    "shrimp": "shellfish",
    "wheat": "gluten",
}


def analyze_nutrition(ingredients: list) -> dict:
    """
    Estimate total nutrition for a list of ingredients.
    Each ingredient is a dict with 'name' and 'amount' in grams.
    """
    totals = defaultdict(float)

    for item in ingredients:
        name = item["name"].lower()
        amount = item.get("amount", 100) / 100  # normalize to 100g

        if name in NUTRITION_DB:
            for key, value in NUTRITION_DB[name].items():
                totals[key] += value * amount

    return {k: round(v, 2) for k, v in totals.items()}


def detect_allergens(ingredients: list, user_allergies: list) -> list:
    """
    Detect allergens in a list of ingredients based on user allergies.
    """
    found = []

    for item in ingredients:
        name = item["name"].lower()
        allergen = ALLERGEN_DB.get(name)
        if allergen and allergen in user_allergies:
            found.append({"ingredient": name, "allergen": allergen})

    return found
