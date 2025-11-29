"""
Seasonal finder tool

Status: OPTIONAL for MVP.
Reason: Enhances recipe suggestions by seasonality but not required for core features.
"""
 
def seasonal_finder(recipes: List[Dict[str, Any]], season: str) -> List[Dict[str, Any]]:
    """Find recipes suitable for a given season."""
    # existing code
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class MealHistory:
    """Tool for tracking meal history and analyzing consumption patterns."""

    def __init__(self, persist_file: Optional[str] = None):
        self.meal_data: List[Dict[str, Any]] = []
        self.persist_file = Path(persist_file) if persist_file else None

        if self.persist_file and self.persist_file.exists():
            try:
                with open(self.persist_file, "r", encoding="utf-8") as f:
                    self.meal_data = json.load(f)
                    # Convert date strings back to date objects
                    for m in self.meal_data:
                        m["date"] = datetime.fromisoformat(m["date"]).date()
            except (OSError, json.JSONDecodeError) as e:
                logger.exception("Could not load meal history: %s", e)

    def _save(self):
        if self.persist_file:
            try:
                data_to_save = [
                    {**m, "date": m["date"].isoformat()} for m in self.meal_data
                ]
                with open(self.persist_file, "w", encoding="utf-8") as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            except OSError as e:
                logger.exception("Could not save meal history: %s", e)

    def add_meal(
        self,
        meal_name: str,
        recipe_id: str,
        day: Optional[str] = None,
        meal_type: Optional[str] = None,
        eaten_date: Optional[date] = None
    ):
        eaten_date = eaten_date or datetime.today().date()
        day = day or eaten_date.strftime("%A")
        self.meal_data.append({
            "meal_name": meal_name,
            "recipe_id": recipe_id,
            "day": day,
            "meal_type": meal_type,
            "date": eaten_date
        })
        self._save()

    def meals_on_date(self, target_date: date) -> List[Dict]:
        return [meal for meal in self.meal_data if meal["date"] == target_date]

    def meals_on_day(self, target_day: str) -> List[Dict]:
        return [meal for meal in self.meal_data if meal["day"].lower() == target_day.lower()]

    def count_meal_freq(self) -> Dict[str, int]:
        freq = {}
        for meal in self.meal_data:
            name = meal["meal_name"]
            freq[name] = freq.get(name, 0) + 1
        return freq

    def most_frequent_meals(self, top_n: int = 1) -> List[Dict]:
        freq = self.count_meal_freq()
        result = []
        for name, count in freq.items():
            recipe_ids = list({m["recipe_id"] for m in self.meal_data if m["meal_name"] == name})
            result.append({
                "meal_name": name,
                "recipe_ids": recipe_ids,
                "count": count
            })
        result.sort(key=lambda x: x["count"], reverse=True)
        return result[:top_n]

    def meals_in_range(self, start_date: date, end_date: date) -> List[Dict]:
        return [
            meal for meal in self.meal_data
            if start_date <= meal["date"] <= end_date
        ]
