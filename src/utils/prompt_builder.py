"""Small prompt builder utilities used by tests to validate prompt templates.

These functions assemble prompt text following conventions described in
`docs/NOTES.md`. They are intentionally lightweight and deterministic so
unit tests can validate prompt structure without calling external LLMs.
"""
from typing import List, Dict, Any


def build_receipt_processing_prompt(file_desc: str = "receipt image", user_note: str | None = None) -> str:
    parts = [
        "You are SmartBites assistant. The user uploaded a receipt.",
        f"Input: {file_desc}",
        "Goal: Extract store_name, purchase_date, items (name, section, quantity, unit_price, total_price), subtotal, total.",
        "Steps: 1) Run OCR on the image. 2) Parse structured fields via NLP. 3) Validate totals against detected numbers.",
        "Output: JSON with keys: store_name, purchase_date, items, subtotal, discounts, total, raw_ocr_text, parsing_confidence.",
    ]
    if user_note:
        parts.append(f"User note: {user_note}")
    return "\n".join(parts)


def build_mealplan_prompt(pantry_snapshot: List[str], days: int = 7, people: int = 2, meals_per_day: int = 3, diet: str | None = None) -> str:
    parts = [
        "You are SmartBites assistant. Given a pantry (list of ingredients with quantities and units), user constraints (diet, allergies), and requested date range + meals per day, propose recipes for each meal slot.",
        f"Days: {days}, Servings: {people}, Meals per day: {meals_per_day}",
        f"Pantry snapshot (normalized): {', '.join(pantry_snapshot[:20])}" if pantry_snapshot else "Pantry snapshot: (empty)",
        "Constraints: Prefer recipes that use only pantry ingredients. If not possible, include a minimal missing ingredient list.",
        "Output JSON shape: {\"plan\": [{\"date\": \"YYYY-MM-DD\", \"meals\": {...}}], \"missingItems\": [] }",
    ]
    if diet:
        parts.insert(1, f"Diet constraint: {diet}")
    return "\n".join(parts)


def build_add_ingredients_prompt(items: List[Dict[str, Any]]) -> str:
    parts = ["Add these ingredients to pantry. Normalize names and units."]
    for it in items:
        name = it.get('name')
        qty = it.get('quantity')
        unit = it.get('unit')
        parts.append(f"- {name} | qty: {qty} | unit: {unit}")
    parts.append("If fields missing, mark as pending and ask the user for clarification.")
    return "\n".join(parts)


def build_modify_meal_plan_prompt(day: str, meal_slot: str, reason: str | None = None) -> str:
    parts = [
        f"User request: Change {day} {meal_slot}.",
        "Follow-up questions: Which day/meal? Replace with what? Any dietary constraints?",
        "Process: propose alternatives, update plan after confirmation, optionally add missing items to shopping list.",
    ]
    if reason:
        parts.append(f"User reason: {reason}")
    return "\n".join(parts)


def build_ate_item_prompt(item_name: str, quantity: float | None = None, when: str | None = None) -> str:
    q = f"User: I ate {quantity or 'some'} of {item_name}"
    if when:
        q += f" at {when}"
    parts = [q, "Process: Deduct quantity from pantry, if negative prompt user to restock, and if it affects planned meals propose replacements."]
    return "\n".join(parts)


def build_shopping_list_prompt(action: str, item: str, quantity: Any = None) -> str:
    parts = [f"Action: {action}", f"Item: {item}"]
    if quantity is not None:
        parts.append(f"Quantity: {quantity}")
    parts.append("Process: CRUD operations on shopping_list; group by section when returning view.")
    return "\n".join(parts)


def build_cooking_helper_prompt(question: str, context: Dict[str, Any] | None = None) -> str:
    parts = [
        "You are a cooking assistant. Answer concisely with steps and temperatures when applicable.",
        f"User question: {question}",
    ]
    if context:
        parts.append(f"Context: {context}")
    parts.append("If follow-up needed, ask for cut/thickness/method.")
    return "\n".join(parts)
