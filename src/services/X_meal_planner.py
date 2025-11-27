
# no idea yet 
"""
Meal Planner Service
----------------------

Purpose: Generate weekly meal plans.

"""

from typing import List, Dict, Any, Optional
import itertools
import os
import requests
import logging

logger = logging.getLogger(__name__)

# Remote recipes source(s) (set via env RECIPE_SOURCE_URLS or RECIPE_SOURCE_URL), fallback to this local list
# RECIPE_SOURCE_URLS may be a comma-separated list of URLs
_RECIPES_SOURCE = os.environ.get(
    "RECIPE_SOURCE_URLS",
    os.environ.get("RECIPE_SOURCE_URL", "https://example.com/recipes.json"),
)
_RECIPES_URLS = [u.strip() for u in _RECIPES_SOURCE.split(",") if u.strip()]

_LOCAL_FALLBACK_DB: List[Dict[str, Any]] = [
    {
        "name": "Vegetable Stir Fry",
        "ingredients": ["broccoli", "carrot", "bell pepper", "soy sauce", "garlic", "onion"],
        "tags": ["vegetarian", "vegan"],
        "time": 20,
        "servings": 2,
    },
    {
        "name": "Chickpea Salad",
        "ingredients": ["chickpeas", "cucumber", "tomato", "olive oil", "lemon", "parsley"],
        "tags": ["vegetarian", "vegan", "gluten_free"],
        "time": 10,
        "servings": 2,
    },
    {
        "name": "Pasta Primavera",
        "ingredients": ["pasta", "zucchini", "tomato", "parmesan", "olive oil"],
        "tags": ["vegetarian"],
        "time": 25,
        "servings": 2,
    },
    {
        "name": "Grilled Salmon",
        "ingredients": ["salmon", "lemon", "dill", "olive oil"],
        "tags": ["gluten_free"],
        "time": 20,
        "servings": 2,
    },
    {
        "name": "Quinoa Bowl",
        "ingredients": ["quinoa", "black beans", "corn", "avocado", "lime"],
        "tags": ["vegetarian", "gluten_free"],
        "time": 30,
        "servings": 2,
    },
    {
        "name": "Omelette",
        "ingredients": ["eggs", "milk", "cheese", "spinach"],
        "tags": ["gluten_free"],
        "time": 10,
        "servings": 1,
    },
]

# simple in-memory cache
_RECIPE_CACHE: Optional[List[Dict[str, Any]]] = None


def _fetch_recipes_from_remote(url: str, timeout: float = 5.0) -> List[Dict[str, Any]]:
    """Attempt to fetch recipes from a remote JSON endpoint. Expect a list of recipe dicts."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        # if the remote returns a dict with a key like "recipes"
        if isinstance(data, dict) and "recipes" in data and isinstance(data["recipes"], list):
            return data["recipes"]
    except (requests.RequestException, ValueError) as e:
        logger.debug("Failed to fetch or parse remote recipes from %s: %s", url, e)
    return []


def _get_recipe_db() -> List[Dict[str, Any]]:
    """Return cached remote recipes if available, otherwise fallback to local DB.
    Supports multiple source URLs (RECIPE_SOURCE_URLS)."""
    global _RECIPE_CACHE
    if _RECIPE_CACHE is not None:
        return _RECIPE_CACHE

    all_remote = []
    for url in _RECIPES_URLS:
        if not url:
            continue
        remote = _fetch_recipes_from_remote(url)
        if remote:
            all_remote.extend(remote)

    if all_remote:
        # normalize entries minimally: ensure keys exist
        normalized = []
        for r in all_remote:
            if not isinstance(r, dict):
                continue
            normalized.append(
                {
                    "name": r.get("name"),
                    "ingredients": r.get("ingredients", []),
                    "tags": r.get("tags", []),
                    "time": r.get("time", None),
                    "servings": r.get("servings", None),
                }
            )
        _RECIPE_CACHE = normalized if normalized else _LOCAL_FALLBACK_DB
    else:
        _RECIPE_CACHE = _LOCAL_FALLBACK_DB
    return _RECIPE_CACHE


def _filter_by_preferences(recipe: Dict[str, Any], preferences: Dict[str, Any]) -> bool:
    """
    Return True if recipe matches the user's preferences (diet tags and excluded ingredients).
    preferences may contain:
      - diet: str or list of strings (e.g., "vegetarian", "vegan", "gluten_free")
      - exclude_ingredients: list of ingredients to avoid (allergens)
    """
    diet = preferences.get("diet")
    excludes = set(i.lower() for i in preferences.get("exclude_ingredients", []))

    if diet:
        if isinstance(diet, str):
            diets = {diet.lower()}
        else:
            diets = set(x.lower() for x in diet)
        recipe_tags = set(t.lower() for t in recipe.get("tags", []))
        if not diets.issubset(recipe_tags):
            return False

    # exclude if any forbidden ingredient appears in the recipe
    recipe_ings = set(i.lower() for i in recipe.get("ingredients", []))
    if excludes & recipe_ings:
        return False

    return True


def match_ingredients_to_recipes(ingredients: List[str]) -> List[Dict[str, Any]]:
    """
    Return a list of recipes from the DB scored by how many ingredients match the provided pantry.
    Each returned recipe dict will have an added 'match_score' (0..1) and 'missing_ingredients'.
    """
    pantry = set(i.lower() for i in ingredients)
    scored = []
    for r in _get_recipe_db():
        req = set(i.lower() for i in r["ingredients"])
        intersection = pantry & req
        score = len(intersection) / len(req) if req else 0.0
        missing = sorted(list(req - pantry))
        entry = r.copy()
        entry["match_score"] = round(score, 2)
        entry["missing_ingredients"] = missing
        scored.append(entry)

    # sort by highest match_score, then by shorter time
    scored.sort(key=lambda x: (-x["match_score"], x.get("time", 999)))
    return scored


def generate_meal_plan(ingredients: List[str], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate a weekly meal plan (default 7 days) based on pantry ingredients and preferences.

    preferences may contain:
      - diet: str or list (e.g., "vegetarian", "vegan", "gluten_free")
      - exclude_ingredients: list
      - meals_per_day: int (1..3) default 1 (dinner)
      - days: int (1..7) default 7
      - allow_missing_ingredients: bool (default False) -- if False, only recipes that can be made with pantry (no missing ingredients) are suggested.

    Returns a list of day entries:
      {"day": "Monday", "meals": [{"slot": "Dinner", "recipe": "Pasta", "missing_ingredients": [...]}, ...]}
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    num_days = int(preferences.get("days", 7))
    num_days = max(1, min(7, num_days))
    meals_per_day = int(preferences.get("meals_per_day", 1))
    meals_per_day = max(1, min(3, meals_per_day))
    slots_by_count = {
        1: ["Dinner"],
        2: ["Lunch", "Dinner"],
        3: ["Breakfast", "Lunch", "Dinner"],
    }
    slots = slots_by_count[meals_per_day]

    # Compute pantry matches (with missing_ingredients information)
    pantry_matches = match_ingredients_to_recipes(ingredients)

    # Filter pantry_matches by preferences
    pref_filtered = [r for r in pantry_matches if _filter_by_preferences(r, preferences)]

    # By default, only suggest recipes that require no missing ingredients.
    allow_missing = bool(preferences.get("allow_missing_ingredients", False))
    if not allow_missing:
        ranked = [r for r in pref_filtered if not r.get("missing_ingredients")]
    else:
        ranked = pref_filtered

    # If strict "no missing" produced no results, fallback to nearest matches (respect excludes/diet)
    if not ranked:
        # broaden to candidates from DB filtered by preferences (may include recipes with missing ingredients)
        db = _get_recipe_db()
        candidates = [r for r in db if _filter_by_preferences(r, preferences)]
        if not candidates:
            # fallback: ignore diet to give suggestions (but still respect excludes)
            candidates = [r for r in db if _filter_by_preferences(r, {"exclude_ingredients": preferences.get("exclude_ingredients", [])})]

        candidate_names = {c["name"] for c in candidates}
        ranked = [r for r in pantry_matches if r["name"] in candidate_names]

        # if still empty (unlikely), use candidates as-is (without match data)
        if not ranked:
            ranked = []
            for c in candidates:
                entry = c.copy()
                entry["match_score"] = 0.0
                entry["missing_ingredients"] = sorted(list(set(i.lower() for i in c.get("ingredients", [])) - set(i.lower() for i in ingredients)))
                ranked.append(entry)

    # if not enough ranked items, append other candidates (preserve ordering)
    db = _get_recipe_db()
    if len(ranked) < len(db):
        extras = [c for c in db if c["name"] not in {r["name"] for r in ranked}]
        ranked.extend(extras)

    plan = []
    # rotate through ranked recipes to fill days and slots
    recipe_cycle = itertools.cycle(ranked) if ranked else itertools.cycle(db)
    db_len = len(ranked) or len(db)
    for i in range(num_days):
        day_name = days[i]
        day_meals = []
        used_this_day = set()
        for slot in slots:
            # pick next recipe not used already this day
            for _ in range(db_len):
                candidate = next(recipe_cycle)
                if candidate["name"] in used_this_day:
                    continue
                used_this_day.add(candidate["name"])
                day_meals.append(
                    {
                        "slot": slot,
                        "recipe": candidate["name"],
                        "time": candidate.get("time"),
                        "servings": candidate.get("servings"),
                        "missing_ingredients": candidate.get("missing_ingredients", []),
                        "match_score": candidate.get("match_score", 0.0),
                        "tags": candidate.get("tags", []),
                    }
                )
                break
        plan.append({"day": day_name, "meals": day_meals})

    return plan


def schedule_meals(meal_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert a meal_plan (as returned by generate_meal_plan) into a simple schedule.
    Returns a dict with:
      - schedule: { "Monday": {"Breakfast": recipe, ...}, ... }
      - aggregated_shopping_list: sorted list of all missing ingredients across the week
    """
    schedule = {}
    shopping_set = set()
    for day_entry in meal_plan:
        day = day_entry.get("day")
        schedule[day] = {}
        for meal in day_entry.get("meals", []):
            slot = meal.get("slot")
            schedule[day][slot] = {
                "recipe": meal.get("recipe"),
                "time": meal.get("time"),
                "servings": meal.get("servings"),
                "missing_ingredients": meal.get("missing_ingredients", []),
                "match_score": meal.get("match_score", 0.0),
                "tags": meal.get("tags", []),
            }
            for ing in meal.get("missing_ingredients", []):
                shopping_set.add(ing)

    return {
        "schedule": schedule,
        "aggregated_shopping_list": sorted(shopping_set),
    }
