"""
Meal planner tool (moved from `X_meal_planner`).

Contains pure functions for matching recipes to pantry ingredients,
generating meal plans, and scheduling meals. Designed to be independent
from persistence so it can be tested in isolation.
"""

from typing import List, Dict, Any, Optional
import itertools
import requests
import logging

logger = logging.getLogger(__name__)

def _fetch_recipes_from_remote(url: str, timeout: float = 5.0) -> List[Dict[str, Any]]:
    """Attempt to fetch recipes from a remote JSON endpoint. Expect a list of recipe dicts."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
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

    recipe_ings = set(i.lower() for i in recipe.get("ingredients", []))
    if excludes & recipe_ings:
        return False

    return True


def match_ingredients_to_recipes(ingredients: List[str]) -> List[Dict[str, Any]]:
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

    scored.sort(key=lambda x: (-x["match_score"], x.get("time", 999)))
    return scored


def generate_meal_plan(ingredients: List[str], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    num_days = int(preferences.get("days", 7))
    num_days = max(1, min(7, num_days))
    meals_per_day = int(preferences.get("meals_per_day", 1))
    meals_per_day = max(1, min(3, meals_per_day))
    slots_by_count = {1: ["Dinner"], 2: ["Lunch", "Dinner"], 3: ["Breakfast", "Lunch", "Dinner"]}
    slots = slots_by_count[meals_per_day]

    pantry_matches = match_ingredients_to_recipes(ingredients)
    pref_filtered = [r for r in pantry_matches if _filter_by_preferences(r, preferences)]

    allow_missing = bool(preferences.get("allow_missing_ingredients", False))
    if not allow_missing:
        ranked = [r for r in pref_filtered if not r.get("missing_ingredients")]
    else:
        ranked = pref_filtered

    if not ranked:
        db = _get_recipe_db()
        candidates = [r for r in db if _filter_by_preferences(r, preferences)]
        if not candidates:
            candidates = [r for r in db if _filter_by_preferences(r, {"exclude_ingredients": preferences.get("exclude_ingredients", [])})]

        candidate_names = {c["name"] for c in candidates}
        ranked = [r for r in pantry_matches if r["name"] in candidate_names]

        if not ranked:
            ranked = []
            for c in candidates:
                entry = c.copy()
                entry["match_score"] = 0.0
                entry["missing_ingredients"] = sorted(list(set(i.lower() for i in c.get("ingredients", [])) - set(i.lower() for i in ingredients)))
                ranked.append(entry)

    db = _get_recipe_db()
    if len(ranked) < len(db):
        extras = [c for c in db if c["name"] not in {r["name"] for r in ranked}]
        ranked.extend(extras)

    plan = []
    recipe_cycle = itertools.cycle(ranked) if ranked else itertools.cycle(db)
    db_len = len(ranked) or len(db)
    for i in range(num_days):
        day_name = days[i]
        day_meals = []
        used_this_day = set()
        for slot in slots:
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

    return {"schedule": schedule, "aggregated_shopping_list": sorted(shopping_set)}
