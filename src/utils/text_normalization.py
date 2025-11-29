"""Text normalization utilities: basic cleaning for ingredient and item names."""
import re
import unicodedata


def normalize_text(text: str) -> str:
    """Normalize text for matching:

    - Lowercase
    - Remove accents
    - Remove extra whitespace and punctuation
    """
    if not text:
        return ""
    # Normalize unicode accents
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    text = text.lower()
    # Replace punctuation with space
    text = re.sub(r"[\-_,.;:/()\[\]{}]", ' ', text)
    # Remove non-alphanumeric but preserve basic units and %
    text = re.sub(r"[^a-z0-9%\s]", '', text)
    # Collapse whitespace
    text = re.sub(r"\s+", ' ', text).strip()
    return text


def normalize_and_tokenize(text: str):
    """Return normalized text and token list."""
    n = normalize_text(text)
    tokens = [t for t in n.split(' ') if t]
    return n, tokens
