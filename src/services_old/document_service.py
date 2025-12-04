"""
Document Service - Handles PDF/image processing

"""
from langfuse import observe
import filetype
from io import BytesIO
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract

class DocumentService:
    """Service for document processing operations."""

    @observe()
    def validate_file(
        self, 
        file_bytes: bytes, 
        mime_type: str
        ) -> bool:

        """Validate that file is a supported PDF or image."""

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
    def get_file_info(
        self, 
        file_bytes: bytes
        ) -> dict:

        """Get basic file information."""

        return {
            "size_bytes": len(file_bytes),
            "size_kb": len(file_bytes) / 1024,
            "size_mb": len(file_bytes) / (1024 * 1024),
        }

    @observe()
    def extract_text(
        self,
        file_bytes: bytes,
        mime_type: str | None = None
    ) -> str:
        """Extract text from PDF or image.

        If mime_type is not provided, it will be guessed. Uses PyPDF2 for PDFs
        and pytesseract + Pillow for images if available; otherwise returns
        a short hint to use your external multimodal API.
        """

        # determine mime if not provided
        if not mime_type:
            kind = filetype.guess(file_bytes)
            mime_type = kind.mime if kind else None

        if not mime_type:
            raise ValueError("Could not determine file MIME type")

        # normalize common variants
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        # validate file first
        self.validate_file(file_bytes, mime_type)

        if mime_type == "application/pdf":
            try:
                reader = PdfReader(BytesIO(file_bytes))
                text = "\n".join((page.extract_text() or "") for page in reader.pages)
                return text.strip() or "[No text extracted from PDF]"
            except Exception:
                return "[PDF extraction requires PyPDF2 or use external multimodal API]"

        if mime_type.startswith("image/"):
            try:
                img = Image.open(BytesIO(file_bytes))
                return pytesseract.image_to_string(img).strip() or "[No text extracted from image]"
            except Exception:
                return "[Image OCR requires pillow and pytesseract or use external multimodal API]"

        raise ValueError(f"Unsupported file type for extraction: {mime_type}")

