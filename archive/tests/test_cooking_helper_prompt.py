"""
Prompt: Cooking Helper

Excerpt from `docs/NOTES.md`:

Trigger: user asks a cooking question.

Prompt example: "What's the correct doneness for beef ribeye on the pan?"

Follow-up: Ask for cut, thickness, method (pan/oven/grill).

Process:
- Provide temperature/time guidance and step-by-step suggestions.
- No DB changes unless user explicitly uses a suggestion and marks an ingredient consumed.
"""

from src.utils.prompt_builder import build_cooking_helper_prompt


def test_cooking_helper_prompt_requests_followups_and_temperatures():
    prompt = build_cooking_helper_prompt("What's the correct doneness for beef ribeye on the pan?", context={'cut': 'ribeye'})
    assert 'doneness' in prompt or 'doneness' in prompt.lower()
    assert 'temperature' in prompt or 'temperature' in prompt.lower()
    assert 'follow-up' in prompt or 'follow' in prompt.lower()
