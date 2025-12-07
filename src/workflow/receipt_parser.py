"""
Receipt Parser

This service provides a unified workflow for handling supermarket receipts:

- File validation (PDF, JPG, PNG, HEIC)
- Text extraction (PDF or Image)
- Structured receipt parsing using AI (schema defined internally)
- Pantry database updates and Shopping List cleanup

Dependencies (injected):
- AIService: handles AI-based structured extraction
- SupabaseAdapter: handles DB persistence and pantry/shopping list updates

Key Features:
- Automatic quantity normalization
- Graceful handling of missing or partial data
- Logging for audit and debugging
- Langfuse observability for tracing
"""

import logging
from typing import Optional, List
from io import BytesIO

import filetype
from langfuse import observe
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
from dotenv import load_dotenv
import os

from ..services.ai_service import AIService
from ..db.supabase_adapter import SupabaseAdapter

load_dotenv()


class ReceiptParser:
    """Unified service for parsing supermarket receipts and updating pantry/shopping list."""

    def __init__(self):
        # Initialize AI extractor with model from environment
        self.ai = AIService(model_name=os.getenv("MODEL"))

        # Initialize database adapter
        self.db = SupabaseAdapter()

    # ------------------------------------------------------------------ #
    #                          FILE VALIDATION                           #
    # ------------------------------------------------------------------ #

    @observe()
    def validate_file(self, file_bytes: bytes, mime_type: str) -> bool:
        """Validate that the file is supported and not corrupted."""
        if mime_type == "application/pdf":
            if not file_bytes.startswith(b'%PDF'):
                raise ValueError("File is not a valid PDF")
        elif mime_type in ["image/jpeg", "image/png", "image/jpg", "image/heic"]:
            kind = filetype.guess(file_bytes)
            if not kind or kind.mime != mime_type:
                raise ValueError("File is not a valid image")
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")
        return True

    # ------------------------------------------------------------------ #
    #                        TEXT EXTRACTION                             #
    # ------------------------------------------------------------------ #

    @observe()
    def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
        """Extract text from a PDF or Image using PyPDF2 or Tesseract OCR."""
        self.validate_file(file_bytes, mime_type)

        # Normalize MIME type
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        # PDF extraction
        if mime_type == "application/pdf":
            try:
                reader = PdfReader(BytesIO(file_bytes))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                return text.strip() or "[No text extracted from PDF]"
            except Exception:
                logging.exception("PDF extraction failed")
                return "[PDF extraction failed]"

        # Image OCR extraction
        if mime_type.startswith("image/"):
            try:
                img = Image.open(BytesIO(file_bytes))
                return pytesseract.image_to_string(img).strip() or "[No text extracted from image]"
            except Exception:
                logging.exception("Image OCR failed")
                return "[Image OCR failed]"

        raise ValueError(f"Unsupported type for extraction: {mime_type}")

    # ------------------------------------------------------------------ #
    #                   AI STRUCTURED RECEIPT PARSING                    #
    # ------------------------------------------------------------------ #

    @observe()
    def analyze_receipt(self, file_bytes: bytes, mime_type: Optional[str] = None) -> dict:
        """Run full structured receipt parsing using AI."""
        if mime_type is None:
            kind = filetype.guess(file_bytes)
            mime_type = kind.mime if kind else "application/octet-stream"

        self.validate_file(file_bytes, mime_type)

        schema = self._get_receipt_schema()
        data = self.ai.extract_structured(file_bytes=file_bytes, schema=schema, mime_type=mime_type)

        # Normalize quantities and unit prices
        for item in data.get("items", []):
            if item.get("quantity") is None:
                item["quantity"] = 1
            if item.get("unit_price") is None and item.get("total_price") is not None and item["quantity"] == 1:
                item["unit_price"] = item["total_price"]

        return data

    # ------------------------------------------------------------------ #
    #                       DB + PANTRY UPDATES                          #
    # ------------------------------------------------------------------ #

    @observe()
    def process_and_store(self, file_bytes: bytes, mime_type: str, user_id: str) -> dict:
        """
        Analyze receipt, store in database, update pantry, and clean shopping list.
        """
        data = self.analyze_receipt(file_bytes, mime_type=mime_type)

        # Persist receipt row
        receipt_row = None
        try:
            receipt_row = self.db.insert_receipt(user_id, data)
        except Exception as e:
            logging.exception("Failed to persist receipt: %s", e)

        receipt_id = receipt_row.get("id") if receipt_row else None

        # Update pantry and shopping list for each item
        for item in data.get("items", []):
            name = item.get("name")
            if not name:
                continue

            quantity = item.get("quantity") or 1
            unit = item.get("unit") or None
            normalized = self.db._normalize_name(name)

            # Add to pantry
            try:
                self.db.upsert_pantry_item(
                    user_id=user_id,
                    name=name,
                    normalized_name=normalized,
                    quantity=quantity,
                    unit=unit,
                    source_receipt_id=receipt_id
                )
            except Exception as e:
                logging.exception("Pantry update failed: %s", e)

            # Remove from shopping list
            try:
                self.db.remove_shopping_list_item_if_present(
                    user_id=user_id,
                    normalized_name=normalized,
                    quantity=quantity
                )
            except Exception as e:
                logging.exception("Shopping List cleanup failed: %s", e)

        return receipt_row or data

    @observe()
    def _get_receipt_schema(self) -> dict:
        """Return JSON schema for structured receipt extraction."""
        return {
            "store_name": "string or null",
            "purchase_date": "YYYY-MM-DD or null",
            "purchase_time": "HH:MM or null",
            "invoice_number": "string or null",
            "items": [
                {
                    "name": "string",
                    "section": "string or null",
                    "quantity": "number or null",
                    "unit_price": "number or null",
                    "total_price": "number or null"
                }
            ],
            "subtotal": "number or null",
            "discounts": "number or null",
            "total": "number or null",
            "payment_method": "string or null"
        }
