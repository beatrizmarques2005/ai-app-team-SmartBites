"""UserService - profile and preferences management

Lightweight service for user profile CRUD, dietary preferences, favorites
and simple household info. Persists via `SupabaseAdapter` when available and
falls back to safe defaults for demo/mock adapters.
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List
from langfuse import observe
from ..db.supabase_adapter import SupabaseAdapter


class UserService:
    """Manage user profiles, preferences, favorites and household info."""

    def __init__(self, adapter: Optional[SupabaseAdapter] = None):
        self.adapter = adapter or SupabaseAdapter()

    @observe()
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Return the user's profile dict or empty dict if not found.

        Safe for demo adapters which may not have a DB client.
        """
        try:
            if getattr(self.adapter, '_has_table', False):
                resp = self.adapter.client.table('users').select('*').eq('id', user_id).execute()
                data = getattr(resp, 'data', None)
                if data:
                    return data[0]
                return {}

            # fallback: try adapter._data or similar
            return getattr(self.adapter, 'get_user', lambda uid: {})(user_id) or {}
        except Exception:
            return {}

    @observe()
    def update_user_profile(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update or upsert the user's profile. Returns persisted row or payload on demo adapters."""
        payload = dict(data)
        payload['id'] = user_id

        try:
            if getattr(self.adapter, '_has_table', False):
                resp = self.adapter.client.table('users').upsert(payload).execute()
                return getattr(resp, 'data', [payload])[0]

            # demo adapter fallback
            if hasattr(self.adapter, 'upsert_user'):
                return self.adapter.upsert_user(user_id, payload)
            return payload
        except Exception:
            return None

    @observe()
    def set_dietary_preferences(self, user_id: str, allergies: List[str], intolerances: List[str], diet_type: str) -> Optional[Dict[str, Any]]:
        """Set dietary fields on the user's profile.

        Stores `allergies` and `intolerances` as lists and `diet_type` as string.
        """
        profile = self.get_user_profile(user_id) or {}
        profile['allergies'] = allergies
        profile['intolerances'] = intolerances
        profile['diet_type'] = diet_type
        return self.update_user_profile(user_id, profile)

    @observe()
    def add_favorite_recipe(self, user_id: str, recipe_id: str) -> bool:
        """Add a recipe to the user's favorites. Returns True on success."""
        try:
            # If adapter provides a specialized method, prefer it
            if hasattr(self.adapter, 'add_favorite_recipe'):
                return self.adapter.add_favorite_recipe(user_id, recipe_id)

            if getattr(self.adapter, '_has_table', False):
                payload = {'user_id': user_id, 'recipe_id': recipe_id}
                resp = self.adapter.client.table('favorites').insert(payload).execute()
                return bool(getattr(resp, 'data', None))

            return False
        except Exception:
            return False

    @observe()
    def remove_favorite_recipe(self, user_id: str, recipe_id: str) -> bool:
        """Remove a favorite recipe for the user."""
        try:
            if hasattr(self.adapter, 'remove_favorite_recipe'):
                return self.adapter.remove_favorite_recipe(user_id, recipe_id)

            if getattr(self.adapter, '_has_table', False):
                resp = self.adapter.client.table('favorites').delete().eq('user_id', user_id).eq('recipe_id', recipe_id).execute()
                return getattr(resp, 'status_code', None) in (200, 204) or bool(getattr(resp, 'data', None))

            return False
        except Exception:
            return False

    @observe()
    def get_favorite_recipes(self, user_id: str) -> List[Dict[str, Any]]:
        """Return list of favorite recipe rows for the user."""
        try:
            if getattr(self.adapter, '_has_table', False):
                resp = self.adapter.client.table('favorites').select('*').eq('user_id', user_id).execute()
                return getattr(resp, 'data', []) or []

            # fallback: try adapter-provided method
            if hasattr(self.adapter, 'list_favorites'):
                return self.adapter.list_favorites(user_id)

            return []
        except Exception:
            return []

    @observe()
    def get_household_info(self, user_id: str) -> Dict[str, Any]:
        """Return household-related info from the user's profile (e.g., number_of_members)."""
        profile = self.get_user_profile(user_id) or {}
        return {
            'number_of_members': profile.get('number_of_members') or profile.get('household_size') or 1,
            'address': profile.get('address'),
        }

    @observe()
    def update_household_info(self, user_id: str, number_of_members: int) -> Optional[Dict[str, Any]]:
        """Update household size on the user's profile."""
        profile = self.get_user_profile(user_id) or {}
        profile['number_of_members'] = number_of_members
        return self.update_user_profile(user_id, profile)
