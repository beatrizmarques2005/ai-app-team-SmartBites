from datetime import datetime

class RecipeFeedback:
    def __init__(self):
        self.feedback_data: list[dict] = []

    def submit_feedback(self, recipe_id: int, rating: int, comments: str, user_id: int):
        if not 1<=rating<=5:
            raise ValueError("Rating must be an integer between 1 and 5.")
        self.feedback_data.append({
            "recipe_id": recipe_id,
            "rating": rating,
            "comments": comments,
            "user_id": user_id,
            "timestamp": datetime.now()
        })

    def statistics(self, recipe_id:int) -> dict:
        ratings = [feedback["rating"] for feedback in self.feedback_data if feedback["recipe_id"] == recipe_id]
        if not ratings:
            return{
                "average_rating": None,
                "total_feedback": 0,
                "highest_rating": None,
                "lowest_rating": None,
            }

        return {
            "average_rating": sum(ratings) / len(ratings),
            "total_feedback": len(ratings),
            "highest_rating": max(ratings),
            "lowest_rating": min(ratings)
        }

    def all_feedback(self, recipe_id):
        if recipe_id:
            return [feedback for feedback in self.feedback_data if feedback["recipe_id"] ==recipe_id]
        return self.feedback_data