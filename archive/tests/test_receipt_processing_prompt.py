"""
Prompt: Receipt Processing

Excerpt from `docs/NOTES.md`:
"""
"""
Trigger: user uploads a receipt/image or confirms they went shopping.

Prompt example: "I went shopping today — here's the receipt." (file + optional text)

Process (implementation steps):
1. Store original file & metadata (uploader, timestamp).
2. Send image to OCR service → get raw text.
3. Run NLP extraction pipeline to parse: store_name, purchase_date, purchase_time, invoice_number, items (name, section, quantity, unit_price, total_price), subtotal, discounts, total, payment_method.
4. Validate parsed totals vs detected numbers (flag suspicious receipts for review).
5. Persist structured receipt to `receipts` DB table.
6. For each parsed item: run `IngredientMatchingUtils` to normalize name and decide if it is a food ingredient.
7. Add food items to `pantry` (create or update quantity). Use `UnitConversionUtils` to standardize quantities.
8. Remove matching items from `shopping_list` if present (and quantities align).
9. Emit event `receipt.processed` for downstream systems (notifications, metrics).
"""

from src.utils.prompt_builder import build_receipt_processing_prompt


def test_receipt_processing_prompt_contains_ocr_and_items():
    prompt = build_receipt_processing_prompt('receipt image of supermarket', user_note='I went shopping today')
    assert 'OCR' in prompt or 'Run OCR' in prompt
    assert 'items' in prompt
    assert 'total' in prompt
    assert 'Output: JSON' in prompt
