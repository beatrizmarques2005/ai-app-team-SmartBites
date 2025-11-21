"""
Document Service - Handles PDF/image processing

"""
from langfuse import observe
import filetype

class DocumentService:
    """Service for document processing operations."""

    @observe()
    def validate_file(self, file_bytes: bytes, mime_type: str) -> bool:
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
    def get_file_info(self, file_bytes: bytes) -> dict:
        """Get basic file information."""
        return {
            "size_bytes": len(file_bytes),
            "size_kb": len(file_bytes) / 1024,
            "size_mb": len(file_bytes) / (1024 * 1024),
        }

    @observe()
    def extract_text(self, file_bytes: bytes) -> str:
        """Placeholder for text extraction."""
        return "[Text extraction handled by Gemini multimodal API]"
