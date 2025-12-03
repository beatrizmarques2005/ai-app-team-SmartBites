"""
Prompt: Modify Meal Plan

Excerpt from `docs/NOTES.md`:

Trigger: user requests to change or remove a meal slot.

Prompt example: "Change Wednesday dinner — I don't want to cook."

Follow-up questions the system must ask:
- Which day/meal?
- Replace with what? (quick recipe, takeaway, remove)
- Any dietary/thematic constraints for replacement?

Process:
- If replacement is a recipe from the pantry, propose alternatives.
- If replacement requires shopping, add missing items to `shopping_list` and ask for approval.
- Update plan after user confirmation.
"""

from src.utils.prompt_builder import build_modify_meal_plan_prompt


def test_modify_meal_plan_prompt_mentions_replacement_and_process():
    prompt = build_modify_meal_plan_prompt('Wednesday', 'dinner', reason='dont want to cook')
    assert 'Change Wednesday dinner' in prompt
    assert 'Replace' in prompt or 'replace' in prompt.lower()
    assert 'update plan' in prompt or 'update' in prompt
