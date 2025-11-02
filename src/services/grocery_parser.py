
"""
Grocery Parser Service
----------------------

Purpose: Extract structured data from receipts.

"""

import re
from typing import List, Dict

def parse_receipt(text: str) -> List[Dict]:
    lines = text.split("\n")
    items = []
    current_sector = None
    invoice_number = None
    last_product_line = None

    # Extract invoice number
    invoice_match = re.search(r"Nro:FS\s+(\w+/\d+)", text)
    if invoice_match:
        invoice_number = invoice_match.group(1)

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect sector headers
        if re.match(r"^[A-Z][\w\s]+:", line):
            current_sector = line.replace(":", "").strip()
            i += 1
            continue

        # Detect product line (starts with (A), (C), etc.)
        if re.match(r"^\([A-Z]\)\s+.+", line):
            last_product_line = re.sub(r"^\([A-Z]\)\s*", "", line).strip()
            i += 1
            continue

        # Detect quantity × price line
        qty_price_match = re.match(r"(\d+)\s*[×xX]\s*(\d+[.,]\d{2})", line)
        if qty_price_match and last_product_line:
            quantity = int(qty_price_match.group(1))
            price_per_unit = float(qty_price_match.group(2).replace(",", "."))
            total_price = round(quantity * price_per_unit, 2)

            # Check if next line is total price override
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r"^\d+[.,]\d{2}$", next_line):
                    total_price = float(next_line.replace(",", "."))
                    i += 1

            items.append({
                "invoice_number": invoice_number,
                "sector": current_sector,
                "name": last_product_line,
                "price_per_unit": price_per_unit,
                "total_units": quantity,
                "total_price": total_price
            })

            last_product_line = None
            i += 1
            continue

        # Detect single-line item with price
        single_line_match = re.match(r"^\([A-Z]\)\s+(.+?)\s+(\d+[.,]\d{2})$", line)
        if single_line_match:
            name = single_line_match.group(1).strip()
            price = float(single_line_match.group(2).replace(",", "."))
            items.append({
                "invoice_number": invoice_number,
                "sector": current_sector,
                "name": name,
                "price_per_unit": price,
                "total_units": 1,
                "total_price": price
            })
            last_product_line = None
            i += 1
            continue

        i += 1

    return items

def update_ingredient_database(items: List[Dict]) -> None:
    """
    Placeholder for updating ingredient database.
    """
    for item in items:
        print(f"Updating DB with: {item['name']} - {item['quantity']} {item['unit']}")


def extract_receipt_metadata(text: str) -> Dict:
    """
    Extract metadata like supermarket name, date, and total amount.
    """
    metadata = {}

    # Supermarket name
    match_market = re.search(r"(CONTINENTE|Pingo Doce|Auchan|Intermarché)", text, re.IGNORECASE)
    if match_market:
        metadata["supermarket"] = match_market.group(1).title()

    # Date
    match_date = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    if match_date:
        metadata["date"] = match_date.group(1)

    # Total
    match_total = re.search(r"TOTAL A PAGAR\s*€?\s*(\d+\.?\d*)", text)
    if match_total:
        metadata["total"] = float(match_total.group(1))

    return metadata

