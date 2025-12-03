"""
Prompt: Add Ingredients Without Receipt (Manual)

Excerpt from `docs/NOTES.md`:

Trigger: user says "Add these ingredients" or uses a UI form.

Follow-up questions (when fields missing):
- Ingredient name (mandatory)
- Quantity (ask for unit or allow free text)
- Purchase date (optional)
- Section / category (optional)

Process:
- Validate input; normalize using `TextNormalizationUtils` and `UnitConversionUtils`.
- Save to pantry. If required fields are missing, keep in `pantry.pending` and ask user via chatbot.
"""

from src.utils.prompt_builder import build_add_ingredients_prompt


def test_add_ingredients_prompt_lists_items_and_pending_behavior():
    items = [{'name': 'Milk', 'quantity': 1, 'unit': 'L'}, {'name': 'Flour', 'quantity': None, 'unit': None}]
    prompt = build_add_ingredients_prompt(items)
    assert 'Milk' in prompt
    assert 'Flour' in prompt
    assert 'pending' in prompt or 'clarification' in prompt
