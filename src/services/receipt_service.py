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
        self.doc_service.validate_pdf(file_bytes) if mime_type == "application/pdf" else None

        schema = self._get_receipt_schema()
        data = self.ai_service.extract_structured(file_bytes, schema, mime_type=mime_type)

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
            "items": [
                {
                    "name": "string",
                    "quantity": "number or null",
                    "unit_price": "number or null",
                    "total_price": "number or null"
                }
            ],
            "subtotal": "number or null",
            "tax": "number or null",
            "total": "number or null",
            "payment_method": "string or null"
        }
