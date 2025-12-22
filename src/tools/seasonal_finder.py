"""
Seasonal Finder Module
----------------------

This module provides functionality to detect the current season, annotate recipes with seasonal matches,
and return a seasonal prompt based on the detected or provided season.

"""

import json
import logging
from datetime import date
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def seasonal_finder(recipes: List[Dict[str, Any]] | None, season: str=None) -> Dict[str, Any]:
    """
    Identifies seasonal recipes and generates a seasonal prompt based on the current or specified season.
    This function filters a list of recipes to find seasonal matches and returns a dictionary
    containing the detected season, a motivational seasonal prompt, and the annotated recipes
    with seasonal match indicators.
    Args:
        recipes (List[Dict[str, Any]] | None): A list of recipe dictionaries to be filtered.
            Each recipe should contain at least a "title" key. If None, an empty list is used.
        season (str, optional): The season to filter by. Valid values are "spring", "summer",
            "autumn", or "winter". If not provided, the current season is determined based on
            the current month. Defaults to None.
    Returns:
        Dict[str, Any]: A dictionary containing:
            - "season" (str): The detected or specified season in lowercase.
            - "seasonal_prompt" (str): A descriptive prompt for the detected season.
            - "recipes" (List[Dict[str, Any]]): The input recipes list with each recipe
              annotated with a "seasonal_match" boolean indicating if the season appears
              in the recipe title.
    Examples:
        >>> seasonal_finder([{"title": "Winter Soup"}], season="winter")
        {'season': 'winter', 'seasonal_prompt': 'Warm and hearty recipes...', 'recipes': [{'title': 'Winter Soup', 'seasonal_match': True}]}
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