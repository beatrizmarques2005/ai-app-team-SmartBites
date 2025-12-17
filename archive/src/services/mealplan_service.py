"""MealPlanService - generate and persist meal plans.

This service uses `X_meal_planner.generate_meal_plan` for proposal and
persists plans to Supabase `meal_plans` table.
"""
from typing import Dict, Any, List, Optional
from ..tools_old.meal_planner import generate_meal_plan, schedule_meals
from ..db.supabase_adapter import SupabaseAdapter
from .user_service import UserService


class MealPlanService:
    def __init__(self, adapter: Optional[SupabaseAdapter] = None, user_service: Optional[UserService] = None):
        self.adapter = adapter or SupabaseAdapter()
        # allow injecting a UserService (test/mocks); otherwise construct one using same adapter
        self.user_service = user_service or UserService(adapter=self.adapter)

    def propose_plan(self, ingredients: List[str], preferences: Dict[str, Any], user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Propose a meal plan for given ingredients and preferences.

        If `user_id` is provided the user's dietary preferences and allergies
        will be merged into `preferences` to avoid proposing recipes that
        conflict with their profile.
        """
        prefs = dict(preferences or {})
        if user_id:
            try:
                profile = self.user_service.get_user_profile(user_id) or {}
                # Merge diet_type -> preferences['diet'] (if not already set)
                diet = profile.get('diet_type')
                if diet and not prefs.get('diet'):
                    prefs['diet'] = [d.strip() for d in str(diet).split(',') if d.strip()] if isinstance(diet, str) else diet

                # Merge allergies into preferences so planner can avoid them
                allergies = profile.get('allergies') or []
                if allergies:
                    prefs.setdefault('avoid_allergens', []).extend([a for a in allergies if a])

                # Normalize preferences fields expected by meal planner
                if 'days' not in prefs:
                    prefs.setdefault('days', 3)
            except Exception:
                # If user lookup fails, fallback to provided preferences
                prefs = prefs

        return generate_meal_plan(ingredients, prefs)

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

    # --- Meal history methods (moved from legacy tools) ---
    def add_history_entry(self, user_id: str, date: str, meal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Record a consumed meal in `meal_history`.

        `meal` is a dict describing the meal (e.g., title, ingredients, servings).
        """
        payload = {
            'user_id': user_id,
            'date': date,
            'meal': meal,
        }
        if not getattr(self.adapter, '_has_table', False):
            return payload
        try:
            resp = self.adapter.client.table('meal_history').insert(payload).execute()
            return resp.data[0] if getattr(resp, 'data', None) else None
        except Exception:
            return None

    def list_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent meal history rows for the user."""
        if not getattr(self.adapter, '_has_table', False):
            return []
        try:
            resp = self.adapter.client.table('meal_history').select('*').eq('user_id', user_id).limit(limit).execute()
            return getattr(resp, 'data', []) or []
        except Exception:
            return []

    def remove_history_entry(self, user_id: str, entry_id: str) -> bool:
        """Delete a history entry by id for the given user."""
        if not getattr(self.adapter, '_has_table', False):
            return False
        try:
            resp = self.adapter.client.table('meal_history').delete().eq('id', entry_id).eq('user_id', user_id).execute()
            return getattr(resp, 'status_code', None) in (200, 204) or (getattr(resp, 'data', None) is not None)
        except Exception:
            return False
