
import fitz
from PIL import Image
import pytesseract
import os


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image file using OCR.
    """

    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

def extract_text(file_path: str) -> str:

    if file_path.endswith(".pdf"):
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            page_text = page.get_text()
            if page_text.strip():
                text += page_text
            else:
                # fallback to OCR
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text += pytesseract.image_to_string(img)
        return text
    elif file_path.lower().endswith((".png", ".jpg", ".jpeg")):
        return extract_text_from_image(file_path)
    else:
        raise ValueError("Unsupported file type")
