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


def seasonal_finder(recipes: List[Dict[str, Any]] | None, season: str=None) -> Dict[str, Any]:
    """
    Detect season, annotate recipes with match, and return a seasonal prompt.
    If 'season' is not passed, determines season based on today's date.
    """
    if not season:
        month = date.today().month
        if month in (12, 1, 2):
            season = "winter"
        elif month in (3,4,5):
            season="spring"
        elif month in (6,7,8):
            season = "summer"
        else:
            season="autumn"
        
    season = season.lower()
    prompts = {
        "spring": "Fresh and light recipes perfect for springtime",
        "summer": "Refreshing and vibrant recipes, ideal for summer days",
        "autumn": "Confort meals with seasonal autumn ingredients",
        "winter": "Warm and hearty recipes to enjoy during winter"
    }

    seasonal_prompt = prompts.get(season, "No specific season detected")

    annot = []
    recipes = recipes or []
    for recipe in recipes:
        title = (recipe.get("title") or "").lower()
        match = season in title
        annot.append({**recipe, "seasonal_match": match})
    
    return {"season": season, "seasonal_prompt": seasonal_prompt, "recipes": annot}