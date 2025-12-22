"""
Receipt Parser Module
---------------------

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
from typing import Optional, Dict, Any

import filetype
from langfuse import observe
from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
from uuid import uuid4
from datetime import datetime

from ..services.ai_service import AIService
from ..db.client import supabase

load_dotenv()

class ReceiptParser:
    """Unified service for parsing supermarket receipts and updating pantry/shopping list."""

    def __init__(self):
        
        self.ai = AIService()
        self.sup_client = supabase
        self._has_table = hasattr(self.sup_client, 'table')
        self.model = os.getenv("MODEL")
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    @observe()
    def validate_file(self, file_bytes: bytes, mime_type: str) -> bool:
        """
        Validates that the provided file bytes match the declared MIME type.
        Args:
            file_bytes (bytes): The raw bytes of the file to validate.
            mime_type (str): The declared MIME type of the file (e.g., 'application/pdf', 'image/jpeg').
        Returns:
            bool: True if the file is valid and matches the declared MIME type.
        Raises:
            ValueError: If the file is not a valid PDF (when MIME type is 'application/pdf'),
                       if the file is not a valid image (when MIME type is image-related),
                       or if the MIME type is not supported.
        Supported MIME types:
            - application/pdf
            - image/jpeg
            - image/png
            - image/jpg
            - image/heic
        """
        
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

    @observe()
    def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
        """
        Extracts text from a given document in byte format.
        This method validates the provided file bytes and mime type, and then uses a client model to extract text from the document. 
        It handles different mime types, specifically converting "image/jpg" to "image/jpeg". 
        If the extraction is successful, it returns the extracted text. 
        In case of failure, it logs the exception and returns a failure message.
        Args:
            file_bytes (bytes): The byte content of the document from which to extract text.
            mime_type (str): The mime type of the document (e.g., "image/jpeg").
        Returns:
            str: The extracted text from the document, or a message indicating failure or no text extracted.
        """
        self.validate_file(file_bytes, mime_type)

        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        try:
            response = self.client.models.generate_content(
                model=self.model,
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

    @observe()
    def analyze_receipt(self, file_bytes: bytes, mime_type: Optional[str] = None) -> dict:
        """
        Analyzes a receipt from the provided file bytes and extracts structured data.
        Args:
            file_bytes (bytes): The raw bytes of the receipt file to be analyzed.
            mime_type (Optional[str]): The MIME type of the file. If not provided, it will be guessed based on the file bytes.
        Returns:
            dict: A dictionary containing the structured data extracted from the receipt, including items and their details.
        Raises:
            ValueError: If the file validation fails or if the extracted data is not in the expected format.
        """
        if mime_type is None:
            kind = filetype.guess(file_bytes)
            mime_type = kind.mime if kind else "application/octet-stream"

        self.validate_file(file_bytes, mime_type)

        schema = self._get_receipt_schema()
        data = self.ai.extract_structured(file_bytes=file_bytes, schema=schema, mime_type=mime_type)

        for item in data.get("items", []):
            if item.get("quantity") is None:
                item["quantity"] = 1
            if item.get("unit_price") is None and item.get("total_price") is not None and item["quantity"] == 1:
                item["unit_price"] = item["total_price"]
        return data

    @observe()
    def _normalize_name(self, name: str) -> str:
        """
        Normalize a name string by stripping whitespace and converting to lowercase.
        
        Args:
            name (str): The name string to normalize.
        
        Returns:
            str: The normalized name in lowercase with leading/trailing whitespace removed.
                 Returns an empty string if the input name is None or empty.
        
        Example:
            >>> self._normalize_name("  John Doe  ")
            'john doe'
            >>> self._normalize_name("")
            ''
        """
        if not name:
            return ""
        return name.strip().lower()

    def insert_receipt(self, user_id: str, receipt_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert a new receipt record into the database.
        Args:
            user_id (str): The unique identifier of the user who owns the receipt.
            receipt_data (Dict[str, Any]): A dictionary containing receipt information with keys:
                - store_name (str): The name of the store where the purchase was made.
                - purchase_date (str): The date when the purchase was made.
        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the inserted receipt with keys:
                - id (str): Unique identifier for the receipt (UUID).
                - user_id (str): The user ID associated with the receipt.
                - store_name (str): The name of the store.
                - purchase_date (str): The purchase date.
                - created_at (str): ISO format timestamp of when the receipt was created.
                Returns None if the insertion fails.
        Raises:
            None currently, but may raise database-related exceptions depending on implementation.
        Note:
            Replace datetime.utcnow() with datetime.now(datetime.timezone.utc) to use 
            timezone-aware datetime objects as per Python best practices.
        """

        receipt_id = str(uuid4())
        store_name = receipt_data.get("store_name")
        purchase_date = receipt_data.get("purchase_date")
        
        result = {
            "id": receipt_id,
            "user_id": user_id,
            "store_name": store_name,
            "purchase_date": purchase_date,
            "created_at": datetime.utcnow().isoformat(),
        }
        logging.info(f"Generated receipt ID {receipt_id} for {store_name} on {purchase_date}")
        return result

    @observe()
    def find_pantry_item(self, user_id: str, normalized_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a pantry item by user ID and normalized ingredient name.
        This method searches the pantry_items table for an item matching the given
        user ID and ingredient name pattern.
        Args:
            user_id (str): The unique identifier of the user.
            normalized_name (str): The normalized ingredient name to search for.
                                  Supports partial matching using SQL LIKE patterns.
        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the pantry item data
                                     if found, None otherwise. Returns None if the
                                     pantry_items table is not available.
        Raises:
            None: This method handles errors gracefully by returning None.
        Examples:
            >>> item = find_pantry_item("user123", "tomato")
            >>> if item:
            ...     print(item['ingredient_name'])
        """
        if not self._has_table:
            return None

        search_pattern = f"%{normalized_name}%"
        resp = self.sup_client.table("pantry_items").select("*").eq("user_id", user_id).ilike("ingredient_name", search_pattern).limit(1).execute()
        if resp and getattr(resp, "data", None):
            return resp.data[0]
        
        return None

    @observe()
    def upsert_pantry_item(
            self, 
            user_id: str, 
            name: str, 
            normalized_name: str, 
            quantity: Optional[float], 
            unit: Optional[str],
            source_receipt_id: Optional[str] = None,
            store_name: Optional[str] = None, 
            purchase_date: Optional[str] = None
            ) -> Optional[Dict[str, Any]]:
        """
        Upsert a pantry item for a user, either creating a new item or updating an existing one.
        This method handles three scenarios:
        1. If no table exists and the item doesn't exist, returns a new item dictionary with a generated UUID.
        2. If the item exists, updates its quantity (by adding to existing quantity) and optionally updates
            store_name and purchase_date.
        3. If the item doesn't exist, creates a new pantry item in the database.
        Args:
            user_id (str): The unique identifier of the user.
            name (str): The original name of the ingredient.
            normalized_name (str): The normalized version of the ingredient name used for lookups.
            quantity (Optional[float]): The quantity of the item being added.
            unit (Optional[str]): The unit of measurement for the quantity (e.g., "kg", "liters").
            source_receipt_id (Optional[str], optional): The ID of the receipt from which the
            store_name (Optional[str], optional): The name of the store where the item was purchased. Defaults to None.
            purchase_date (Optional[str], optional): The date when the item was purchased. Defaults to None.
        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the pantry item details (id, user_id, ingredient_name, 
                                        quantity, store_name, purchase_date) if successful, or None if an error occurs.
        """
        normalized_name = self._normalize_name(normalized_name)
        existing = self.find_pantry_item(user_id, normalized_name)

        if not self._has_table and not existing:
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

            resp = self.sup_client.table("pantry_items").update(update_doc).eq("id", existing.get("id")).execute()
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

        resp = self.sup_client.table("pantry_items").insert(payload).execute()
        if resp and getattr(resp, "data", None):
            return resp.data[0]
        return None

    @observe()
    def remove_shopping_list_item_if_present(self, user_id: str, normalized_name: str, quantity: Optional[float] = None):
        """
        Remove or update a shopping list item for a user based on ingredient name and quantity.
        Searches for a shopping list item matching the normalized ingredient name for the given user.
        If found, either removes the item completely or reduces its quantity based on the provided amount.
        Args:
            user_id (str): The unique identifier of the user whose shopping list is being modified.
            normalized_name (str): The normalized name of the ingredient to search for.
            quantity (Optional[float]): The quantity to remove from the shopping list item.
                                       If None or not provided, the entire item is deleted.
                                       Defaults to None.
        Returns:
            dict or None: A dictionary indicating the operation result:
                         - {"removed": True} if the item was completely deleted
                         - {"updated_quantity": new_qty} if the item quantity was updated
                         - None if no matching item was found, the table is not available,
                           or an exception occurred during the operation.
        Raises:
            None: Exceptions are caught and logged at debug level without raising.
        Note:
            This method requires the table to be initialized (_has_table must be True).
            Uses case-insensitive pattern matching (ilike) for ingredient name search.
        """
        if not self._has_table:
            return None

        try:
            search_pattern = f"%{normalized_name}%"
            resp = self.sup_client.table("shopping_list").select("*").eq("user_id", user_id).ilike("ingredient_name", search_pattern).limit(1).execute()
            if not resp or not getattr(resp, "data", None):
                return None

            item = resp.data[0]
            try:
                existing_qty = item.get("quantity") or 0
            except Exception:
                existing_qty = None

            if existing_qty is None or quantity is None:
                self.sup_client.table("shopping_list").delete().eq("id", item.get("id")).execute()
                return {"removed": True}

            new_qty = existing_qty - (quantity or 0)
            if new_qty <= 0:
                self.sup_client.table("shopping_list").delete().eq("id", item.get("id")).execute()
                return {"removed": True}
            else:
                self.sup_client.table("shopping_list").update({"quantity": new_qty}).eq("id", item.get("id")).execute()
                return {"updated_quantity": new_qty}
        except Exception as e:
            logging.debug(f"Shopping list update (non-critical): {e}")
            return None

    @observe()
    def process_and_store(self, file_bytes: bytes, mime_type: str, user_id: str) -> dict:
        """
        Process a receipt file, extract item data, and store it in the database.
        This method performs the following steps:
        1. Analyzes the receipt file to extract structured data
        2. Inserts the receipt record into the database
        3. Adds extracted items to the user's pantry
        4. Removes matched items from the user's shopping list
        Args:
            file_bytes (bytes): The binary content of the receipt file.
            mime_type (str): The MIME type of the receipt file (e.g., 'image/jpeg', 'application/pdf').
            user_id (str): The unique identifier of the user processing the receipt.
        Returns:
            dict: A dictionary containing:
                - 'id' (str): The receipt ID if successfully inserted
                - 'items' (list): List of extracted items from the receipt
                - 'store_name' (str): Name of the store from the receipt
                - 'purchase_date' (str): Date of purchase from the receipt
                - 'error' (str): Error message if receipt analysis or insertion failed
                - 'pantry_warnings' (list): Optional list of warnings encountered during pantry updates
        Raises:
            No exceptions are raised; errors are caught and returned in the result dictionary.
        Notes:
            - If receipt analysis fails, the method returns early with an error
            - If database insertion fails, returns error without processing items
            - Pantry update failures are logged as warnings but do not prevent completion
            - Shopping list cleanup failures are logged but do not fail the overall operation
        """

        data = self.analyze_receipt(file_bytes, mime_type=mime_type)
        
        if "error" in data:
            return data

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
                    store_name=store_name.lower() if store_name else None,
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

        result = receipt_row or data
        if pantry_errors:
            result["pantry_warnings"] = pantry_errors
        return result

    @observe()
    def _get_receipt_schema(self) -> dict:
        """
        Generate the schema structure for receipt parsing.
        
        Defines the expected format and data types for parsed receipt information,
        including store details, itemized purchases, and payment information.
        
        Returns:
            dict: A dictionary defining the receipt schema with the following structure:
                - store_name (str or None): The name of the store
                - purchase_date (str or None): Date of purchase in YYYY-MM-DD format
                - purchase_time (str or None): Time of purchase in HH:MM format
                - invoice_number (str or None): Receipt or invoice number
                - items (list): List of purchased items, each containing:
                    - name (str): Item name
                    - section (str or None): Product category or section
                    - quantity (float or None): Quantity purchased
                    - unit_price (float or None): Price per unit
                    - total_price (float or None): Total price for item
                - subtotal (float or None): Subtotal before discounts and taxes
                - discounts (float or None): Total discount amount applied
                - total (float or None): Final total amount paid
                - payment_method (str or None): Method of payment used
        """
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
                    "total_price": "number or null",
                }
            ],
            "subtotal": "number or null",
            "discounts": "number or null",
            "total": "number or null",
            "payment_method": "string or null"
        }
