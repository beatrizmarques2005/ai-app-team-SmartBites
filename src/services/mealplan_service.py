"""MealPlanService - generate and persist meal plans.

This service uses `X_meal_planner.generate_meal_plan` for proposal and
persists plans to Supabase `meal_plans` table.
"""
from typing import Dict, Any, List, Optional
from ..services.X_meal_planner import generate_meal_plan, schedule_meals
from ..db.supabase_adapter import SupabaseAdapter


class MealPlanService:
    def __init__(self, adapter: Optional[SupabaseAdapter] = None):
        self.adapter = adapter or SupabaseAdapter()

    def propose_plan(self, ingredients: List[str], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        return generate_meal_plan(ingredients, preferences)

    def get_schedule_and_shopping(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        return schedule_meals(plan)

    def save_plan(self, user_id: str, start_date: str, end_date: str, plan: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        payload = {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
            "metadata": metadata or {},
            "slots": plan,
        }
        # If adapter is a fallback (no DB present), just return the payload for demo purposes
        if not getattr(self.adapter, '_has_table', False):
            return payload

        resp = self.adapter.client.table('meal_plans').insert(payload).execute()
        if getattr(resp, 'data', None):
            return resp.data[0]
        return None
