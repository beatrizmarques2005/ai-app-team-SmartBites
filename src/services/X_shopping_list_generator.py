"""
Experimental Shopping List Generator

Status: EXPERIMENTAL / optional. The project provides `src/services/shopping_list_service.py`
and `src/db/supabase_adapter.py` for persisted shopping-list operations. This
module is a lightweight prototype and is not required for core functionality.
"""

def generate_shopping_list(meal_plan: list, inventory: list) -> list:
    # placeholder prototype
    needed = []
    for day in meal_plan:
        for meal in day.get('meals', []):
            for ing in meal.get('missing_ingredients', []):
                needed.append(ing)
    # simple dedupe
    return sorted(list(set(needed)))


def format_shopping_list(items: list) -> dict:
    return {"items": items, "count": len(items)}

