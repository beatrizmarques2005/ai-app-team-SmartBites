"""
Prompt: Shopping List Management

Excerpt from `docs/NOTES.md`:

Trigger: user adds/removes items manually or via auto-add from meal planning.

Prompt example: "Add milk 1L to my shopping list." or "Remove eggs"

Process:
- CRUD operations on `shopping_list` table.
- Support grouping by store section (optional) for better UX when viewing list.
- When a receipt is added, sync to remove purchased items.
"""

from src.utils.prompt_builder import build_shopping_list_prompt


def test_shopping_list_prompt_crud_and_grouping():
    prompt = build_shopping_list_prompt('Add', 'milk', '1L')
    assert 'Action: Add' in prompt
    assert 'Item: milk' in prompt or 'milk' in prompt
    assert 'CRUD' in prompt or 'group by' in prompt or 'group' in prompt
