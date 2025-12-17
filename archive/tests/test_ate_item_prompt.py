"""
Prompt: Ate an Item Not in Plan

Excerpt from `docs/NOTES.md`:

Trigger: user reports consumption outside plan.

Prompt example: "I ate 2 slices of bread at 10:30."

Follow-up questions:
- What exactly was consumed? (clarify brand/type if ambiguous)
- Quantity (approx.)
- When?

Process:
- Deduct quantity from pantry (or mark as unknown). If quantity becomes negative, prompt user to restock or update.
- If the consumed ingredient was planned for a future meal: flag the meal slot and propose replacements using available pantry items.
"""

from src.utils.prompt_builder import build_ate_item_prompt


def test_ate_item_prompt_deducts_and_prompts_for_negative():
    prompt = build_ate_item_prompt('bread', 2, when='10:30')
    assert 'I ate' in prompt or 'ate' in prompt
    assert 'Deduct' in prompt or 'deduct' in prompt.lower()
    assert 'restock' in prompt or 'restock' in prompt.lower()
