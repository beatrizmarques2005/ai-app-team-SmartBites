"""
Services package - Business logic layer

All domain-specific logic lives here.
Services orchestrate AI calls, tools, and business rules.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.services.ai_service import AIService

__all__ = [
    'AIService',
]
