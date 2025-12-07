"""
Receipt Parser
This class performs:
- File validation (PDF, JPG, PNG, HEIC)
- Text extraction (PDF or Image)
- Structured receipt parsing using AI (schema defined inside)
- Pantry DB updates + Shopping List cleanup

Dependencies (injected):
- AIService
- SupabaseAdapter
"""

import logging
from typing import Optional
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
    """Unified service to parse supermarket receipts."""

    def __init__(
        self,
    ):
        # AI extractor
        self.ai = AIService(model_name=os.getenv("MODEL"))

        # DB adapter
        self.db = SupabaseAdapter()

    # ------------------------------------------------------------------ #
    #                          FILE VALIDATION                           #
    # ------------------------------------------------------------------ #

    @observe()
    def validate_file(
        self,
        file_bytes: bytes,
        mime_type: str
    ) -> bool:
        """Check that file is supported and not corrupted."""

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
    def extract_text(
        self,
        file_bytes: bytes,
        mime_type: str
    ) -> str:
        """Extract text from a PDF or Image using PyPDF2 / Tesseract OCR."""

        self.validate_file(file_bytes, mime_type)

        # normalize
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        # PDFs
        if mime_type == "application/pdf":
            try:
                reader = PdfReader(BytesIO(file_bytes))
                text = "\n".join((page.extract_text() or "") for page in reader.pages)
                return text.strip() or "[No text extracted from PDF]"
            except Exception:
                return "[PDF extraction failed]"

        # Images
        if mime_type.startswith("image/"):
            try:
                img = Image.open(BytesIO(file_bytes))
                return pytesseract.image_to_string(img).strip() or "[No text extracted from image]"
            except Exception:
                return "[Image OCR failed]"

        raise ValueError(f"Unsupported type for extraction: {mime_type}")

    # ------------------------------------------------------------------ #
    #                   AI STRUCTURED RECEIPT PARSING                    #
    # ------------------------------------------------------------------ #

    @observe()
    def analyze_receipt(
        self,
        file_bytes: bytes,
        mime_type: str = None
    ) -> dict:
        """Run full structured receipt parsing using AI."""

        # Detect mime if not given
        if mime_type is None:
            kind = filetype.guess(file_bytes)
            mime_type = kind.mime if kind else "application/octet-stream"

        # Validate file
        self.validate_file(file_bytes, mime_type)

        # Ask AI for structured schema output
        schema = self._receipt_schema()
        data = self.ai.extract_structured(
            file_bytes=file_bytes,
            schema=schema,
            mime_type=mime_type
        )

        # Normalize items
        for item in data.get("items", []):
            if item.get("quantity") is None:
                item["quantity"] = 1

            if (
                item.get("unit_price") is None and
                item.get("total_price") is not None and
                item["quantity"] == 1
            ):
                item["unit_price"] = item["total_price"]

        return data

    # ------------------------------------------------------------------ #
    #                       DB + PANTRY UPDATES                          #
    # ------------------------------------------------------------------ #

    @observe()
    def process_and_store(
        self,
        file_bytes: bytes,
        mime_type: str,
        user_id: str
    ) -> dict:
        """
        Analyze receipt + store in DB + update pantry & shopping list.
        """

        # First get structured receipt data
        data = self.analyze_receipt(file_bytes, mime_type=mime_type)

        # Try to persist receipt row
        receipt_row = None
        try:
            receipt_row = self.db.insert_receipt(user_id, data)
        except Exception as e:
            logging.exception("Failed to persist receipt: %s", e)

        receipt_id = receipt_row.get("id") if receipt_row else None

        # For every item detected
        for item in data.get("items", []):
            name = item.get("name")
            if not name:
                continue

            quantity = item.get("quantity") or 1
            unit = item.get("unit") or None
            normalized = self.db._normalize_name(name)

            # ---- Add to pantry ---- #
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

            # ---- Remove from shopping list ---- #
            try:
                self.db.remove_shopping_list_item_if_present(
                    user_id=user_id,
                    normalized_name=normalized,
                    quantity=quantity
                )
            except Exception as e:
                logging.exception("Shopping List cleanup failed: %s", e)

        return receipt_row or data
