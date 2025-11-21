"""
Receipt Service - Supermarket receipt domain logic

This service orchestrates:
- AI extraction
- Document validation
- Business rules

It's domain-specific - knows about receipts.
"""

from langfuse import observe
from .ai_service import AIService
from .document_service import DocumentService

class ReceiptService:
    """Service for analyzing supermarket receipts."""

    def __init__(self, model: str = "gemini-2.5-flash-lite"):
        """Initialize receipt service with dependencies.

        Args:
            model: Gemini model to use
        """
        self.ai_service = AIService(model=model)
        self.doc_service = DocumentService()

    @observe()
    def analyze_receipt(self, file_bytes: bytes, mime_type: str = "application/pdf") -> dict:
        """Complete receipt analysis pipeline.

        Args:
            file_bytes: Receipt file bytes
            mime_type: MIME type (PDF or image)

        Returns:
            Structured receipt data
        """
        # Auto-detect MIME type if not provided
        if mime_type is None:
            kind = filetype.guess(file_bytes)
            mime_type = kind.mime if kind else "application/octet-stream"

        # Validate file
        self.doc_service.validate_file(file_bytes, mime_type)

        # Extract structured data
        schema = self._get_receipt_schema()
        data = self.ai_service.extract_structured(file_bytes, schema, mime_type=mime_type)

        # Normalize items
        for item in data.get("items", []):
            if item.get("quantity") is None:
                item["quantity"] = 1
            if item.get("unit_price") is None and item.get("total_price") is not None and item["quantity"] == 1:
                item["unit_price"] = item["total_price"]

        return data

    @observe()
    def answer_question(self, question: str, receipt_data: dict) -> str:
        """Answer question about a receipt.

        Args:
            question: User's question
            receipt_data: Receipt data for context

        Returns:
            AI's answer
        """
        system_instruction = """You are a helpful assistant analyzing supermarket receipts.
                                Answer questions based on the provided receipt data.
                                If information is not present, say so."""

        return self.ai_service.chat_with_context(
            question,
            receipt_data,
            system_instruction
        )

    def _get_receipt_schema(self) -> dict:
        """Define receipt extraction schema.

        Returns:
            JSON schema for receipt data
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
                    "total_price": "number or null"
                }
            ],
            "subtotal": "number or null",
            "discounts": "number or null",
            "total": "number or null",
            "payment_method": "string or null"
        }

