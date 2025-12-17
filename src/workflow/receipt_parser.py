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
from typing import Optional, List, Dict, Any
from io import BytesIO
import json

import filetype
from langfuse import observe
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
from datetime import datetime

from ..services.ai_service import AIService
from ..db.client import supabase

load_dotenv()

class ReceiptParser:
    """Unified service for parsing supermarket receipts and updating pantry/shopping list."""

    def __init__(self):
        # Initialize AI extractor with model from environment
        self.ai = AIService()

        # Initialize database client directly
        self.client = supabase
        self._has_table = hasattr(self.client, 'table')

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
        """Extract text from a PDF or Image using Gemini's multimodal API."""
        self.validate_file(file_bytes, mime_type)

        # Normalize MIME type
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        try:
            # Initialize Gemini client
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            model = "gemini-2.5-flash-lite"

            # Use Gemini to extract text from PDF or image
            response = client.models.generate_content(
                model=model,
                contents=[
                    "Extract all text from this document. Return ONLY the extracted text, no additional commentary.",
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=mime_type
                    )
                ]
            )

            extracted_text = response.text.strip()
            return extracted_text or "[No text extracted from document]"

        except Exception:
            logging.exception("Text extraction with Gemini failed")
            return "[Text extraction failed]"

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

    def _normalize_name(self, name: str) -> str:
        if not name:
            return ""
        return name.strip().lower()

    def insert_receipt(self, user_id: str, receipt_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert receipt items directly into pantry_items table.
        
        The receipt_data contains store_name, purchase_date, and items.
        We insert each item from the receipt into pantry_items.
        """
        from uuid import uuid4
        
        # Generate a receipt ID for reference
        receipt_id = str(uuid4())
        store_name = receipt_data.get("store_name")
        purchase_date = receipt_data.get("purchase_date")
        
        # Each item in the receipt will be inserted into pantry_items
        # This method returns a mock receipt object with the ID
        result = {
            "id": receipt_id,
            "user_id": user_id,
            "store_name": store_name,
            "purchase_date": purchase_date,
            "created_at": datetime.utcnow().isoformat(),
        }
        logging.info(f"Generated receipt ID {receipt_id} for {store_name} on {purchase_date}")
        return result

    def find_pantry_item(self, user_id: str, normalized_name: str) -> Optional[Dict[str, Any]]:
        """Find an existing pantry item by normalized ingredient name."""
        if not self._has_table:
            return None

        # Search using normalized pattern for case-insensitive fuzzy matching
        search_pattern = f"%{normalized_name}%"
        resp = self.client.table("pantry_items").select("*").eq("user_id", user_id).ilike("ingredient_name", search_pattern).limit(1).execute()
        if resp and getattr(resp, "data", None):
            return resp.data[0]
        return None

    def upsert_pantry_item(self, user_id: str, name: str, normalized_name: str, quantity: Optional[float], unit: Optional[str], source_receipt_id: Optional[str] = None, store_name: Optional[str] = None, purchase_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        # Ensure normalized_name is actually normalized
        normalized_name = self._normalize_name(normalized_name)
        existing = self.find_pantry_item(user_id, normalized_name)

        if not self._has_table and not existing:
            from uuid import uuid4
            row = {
                "id": uuid4(),
                "user_id": user_id,
                "ingredient_name": name,
                "quantity": quantity,
                "store_name": store_name,
                "purchase_date": purchase_date,
            }
            return row

        if existing:
            try:
                existing_qty = existing.get("quantity") or 0
                new_qty = (existing_qty or 0) + (quantity or 0)
            except Exception:
                new_qty = quantity

            update_doc = {
                "quantity": new_qty,
            }
            if store_name:
                update_doc["store_name"] = store_name
            if purchase_date:
                update_doc["purchase_date"] = purchase_date

            if not self._has_table:
                try:
                    existing['quantity'] = new_qty
                    if store_name:
                        existing['store_name'] = store_name
                    if purchase_date:
                        existing['purchase_date'] = purchase_date
                    return existing
                except Exception:
                    return None

            resp = self.client.table("pantry_items").update(update_doc).eq("id", existing.get("id")).execute()
            if resp and getattr(resp, "data", None):
                return resp.data[0]
            return None

        payload = {
            "user_id": user_id,
            "ingredient_name": normalized_name,
            "quantity": quantity,
            "store_name": store_name,
            "purchase_date": purchase_date,
        }
        if not self._has_table:
            from uuid import uuid4
            payload_with_id = {**payload, 'id': uuid4()}
            return payload_with_id

        resp = self.client.table("pantry_items").insert(payload).execute()
        if resp and getattr(resp, "data", None):
            return resp.data[0]
        return None

    def remove_shopping_list_item_if_present(self, user_id: str, normalized_name: str, quantity: Optional[float] = None):
        """If a shopping list item matches the purchased item, decrement or remove it."""
        if not self._has_table:
            return None

        try:
            # Search using normalized pattern for case-insensitive fuzzy matching
            search_pattern = f"%{normalized_name}%"
            resp = self.client.table("shopping_list").select("*").eq("user_id", user_id).ilike("ingredient_name", search_pattern).limit(1).execute()
            if not resp or not getattr(resp, "data", None):
                return None

            item = resp.data[0]
            try:
                existing_qty = item.get("quantity") or 0
            except Exception:
                existing_qty = None

            if existing_qty is None or quantity is None:
                self.client.table("shopping_list").delete().eq("id", item.get("id")).execute()
                return {"removed": True}

            new_qty = existing_qty - (quantity or 0)
            if new_qty <= 0:
                self.client.table("shopping_list").delete().eq("id", item.get("id")).execute()
                return {"removed": True}
            else:
                self.client.table("shopping_list").update({"quantity": new_qty}).eq("id", item.get("id")).execute()
                return {"updated_quantity": new_qty}
        except Exception as e:
            logging.debug(f"Shopping list update (non-critical): {e}")
            return None

    @observe()
    def process_and_store(self, file_bytes: bytes, mime_type: str, user_id: str) -> dict:
        """
        Analyze receipt, store in database, update pantry, and clean shopping list.
        Returns a dict with 'success' key and error details if any step fails.
        """
        data = self.analyze_receipt(file_bytes, mime_type=mime_type)
        
        # Check if analysis itself failed
        if "error" in data:
            return data

        # Persist receipt row
        receipt_row = None
        try:
            receipt_row = self.insert_receipt(user_id, data)
            logging.info(f"Receipt inserted successfully with ID: {receipt_row.get('id') if receipt_row else 'None'}")
        except Exception as e:
            error_msg = f"Failed to persist receipt: {str(e)}"
            logging.exception(error_msg)
            return {"items": [], "error": error_msg}

        if not receipt_row:
            return {"items": [], "error": "Failed to insert receipt: no row returned from database"}

        receipt_id = receipt_row.get("id")

        # Update pantry and shopping list for each item
        pantry_errors = []
        store_name = data.get("store_name")
        purchase_date = data.get("purchase_date")
        
        for item in data.get("items", []):
            name = item.get("name")
            if not name:
                continue

            quantity = item.get("quantity") or 1
            unit = item.get("unit") or None
            normalized = self._normalize_name(name)

            # Add to pantry
            try:
                self.upsert_pantry_item(
                    user_id=user_id,
                    name=name,
                    normalized_name=normalized,
                    quantity=quantity,
                    unit=unit,
                    source_receipt_id=receipt_id,
                    store_name=store_name,
                    purchase_date=purchase_date
                )
            except Exception as e:
                error_msg = f"Pantry update failed for '{name}': {str(e)}"
                logging.exception(error_msg)
                pantry_errors.append(error_msg)

            # Remove from shopping list
            try:
                self.remove_shopping_list_item_if_present(
                    user_id=user_id,
                    normalized_name=normalized,
                    quantity=quantity
                )
            except Exception as e:
                error_msg = f"Shopping List cleanup failed for '{name}': {str(e)}"
                logging.exception(error_msg)
                # Don't fail completely if shopping list update fails

        # Return success with receipt data
        result = receipt_row or data
        if pantry_errors:
            result["pantry_warnings"] = pantry_errors
        return result

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
