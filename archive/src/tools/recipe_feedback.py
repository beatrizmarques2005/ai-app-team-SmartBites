import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class RecipeFeedback:
    """Tool for managing and analyzing recipe feedback.

    Status: OPTIONAL for MVP.
    Reason: Helps collect user recipe ratings; useful but not required for initial flows.
    """

    def __init__(self, persist_file: Optional[str] = None):
        """
        Args:
            persist_file: Optional path to JSON file for persistence.
        """
        self.feedback_data: List[Dict[str, Any]] = []
        self.persist_file = Path(persist_file) if persist_file else None

        if self.persist_file and self.persist_file.exists():
            try:
                with open(self.persist_file, "r", encoding="utf-8") as f:
                    self.feedback_data = json.load(f)
                    # Convert timestamps back to datetime
                    for fb in self.feedback_data:
                        fb["timestamp"] = datetime.fromisoformat(fb["timestamp"])
            except (OSError, json.JSONDecodeError) as e:
                logger.exception("Could not load feedback file: %s", e)

    def _save(self):
        """Persist feedback to JSON file."""
        if self.persist_file:
            try:
                with open(self.persist_file, "w", encoding="utf-8") as f:
                    # Convert datetime to ISO string
                    data_to_save = [
                        {**fb, "timestamp": fb["timestamp"].isoformat()} for fb in self.feedback_data
                    ]
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            except OSError as e:
                logger.exception("Could not save feedback: %s", e)

    def submit_feedback(
        self,
        recipe_id: int,
        rating: int,
        comments: str,
        user_id: int,
        tags: Optional[List[str]] = None
    ):
        """Add a new feedback entry."""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be an integer between 1 and 5.")
        comments = comments.strip() or "No comment provided."
        entry = {
            "recipe_id": recipe_id,
            "rating": rating,
            "comments": comments,
            "user_id": user_id,
            "tags": tags or [],
            "timestamp": datetime.now()
        }
        self.feedback_data.append(entry)
        self._save()

    def all_feedback(
        self,
        recipe_id: Optional[int] = None,
        sort_by_time: bool = True,
        descending: bool = True
    ) -> List[Dict]:
        """Return all feedback, optionally filtered by recipe_id."""
        data = [
            fb for fb in self.feedback_data
            if recipe_id is None or fb["recipe_id"] == recipe_id
        ]
        if sort_by_time:
            data.sort(key=lambda x: x["timestamp"], reverse=descending)
        return data

    def statistics(self, recipe_id: int) -> Dict[str, Optional[float]]:
        """Return aggregated statistics for a specific recipe."""
        ratings = [fb["rating"] for fb in self.feedback_data if fb["recipe_id"] == recipe_id]
        if not ratings:
            return {
                "average_rating": None,
                "total_feedback": 0,
                "highest_rating": None,
                "lowest_rating": None,
            }
        return {
            "average_rating": round(sum(ratings) / len(ratings), 2),
            "total_feedback": len(ratings),
            "highest_rating": max(ratings),
            "lowest_rating": min(ratings)
        }

    def global_statistics(self) -> Dict[str, Optional[float]]:
        """Return aggregated statistics across all recipes."""
        all_ratings = [fb["rating"] for fb in self.feedback_data]
        if not all_ratings:
            return {"average_rating": None, "total_feedback": 0}
        return {"average_rating": round(sum(all_ratings) / len(all_ratings), 2),
                "total_feedback": len(all_ratings)}

    def filter_by_tag(self, tag: str) -> List[Dict]:
        """Return feedback entries that contain a specific tag."""
        return [fb for fb in self.feedback_data if tag in fb.get("tags", [])]

