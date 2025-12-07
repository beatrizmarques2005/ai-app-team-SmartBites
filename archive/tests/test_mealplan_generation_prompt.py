"""
Prompt: Meal Plan Generation

Excerpt from `docs/NOTES.md`:

Prompt example: "Generate a 7-day meal plan for 2 people, breakfast/lunch/dinner. Vegetarian, avoid nuts."

Process highlights:
1. Validate constraints and user profile (allergies, diet_type).
2. Pull pantry snapshot and normalize ingredients/quantities.
3. Use `RecipeService.search_recipes_by_ingredients()` with strict mode to find recipes that require only pantry ingredients.
4. If strict mode fails, run a relaxed search and compile `missingItems`.
5. Present proposal with recipes per slot and missing items.
6. On approval, save plan and optionally add missing items to shopping list.
"""

from src.utils.prompt_builder import build_mealplan_prompt


def test_mealplan_prompt_contains_plan_and_missingitems():
    pantry = ['milk', 'eggs', 'rice']
    prompt = build_mealplan_prompt(pantry, days=3, people=2, meals_per_day=3, diet='vegetarian')
    assert 'plan' in prompt.lower() or 'Output JSON' in prompt
    assert 'missingItems' in prompt or 'missing ingredient' in prompt
    assert 'pantry' in prompt.lower()
    assert 'vegetarian' in prompt
