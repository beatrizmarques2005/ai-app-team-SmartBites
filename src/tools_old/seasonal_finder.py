"""Seasonal finder and meal history tools.

This module provides a simple seasonal finder placeholder and a
`MealHistory` helper used by tests and tools. The implementations are
minimal and safe to import in environments without optional deps.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def seasonal_finder(recipes: List[Dict[str, Any]], season: str) -> List[Dict[str, Any]]:
    """Return recipes annotated with whether they match the given season.

    This simple implementation looks for the season keyword in recipe
    metadata (if present). Real implementation can use ingredient seasonality
    maps.
    """
    out = []
    for r in recipes:
        title = (r.get('title') or '').lower()
        match = season.lower() in title
        out.append({**r, 'season_match': match})
    return out