"""Profile Service - Handle user profile operations"""
from typing import Dict, Any, Optional
from ..db.client import supabase
from ..authentication import AuthService


class UserWriter:
    """Service for managing user profiles"""
    
    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if not self.user_id:
            raise ValueError("User must be authenticated.")
        self.client = supabase
    
    def update_user_profile(
        self, 
        full_name: str,
        birth_date: Optional[str] = None,
        gender: Optional[str] = None,
        household_number: int = 1,
        restrictions: list = None,
        diet_type: list = None,
        cuisine_type: list = None
    ) -> Dict[str, Any]:
        """
        Update user profile in database.
        
        Args:
            full_name: User's full name
            birth_date: Birth date in YYYY-MM-DD format
            gender: User's gender
            household_number: Number of people in household
            restrictions: List of dietary restrictions
            diet_type: List of diet types
            cuisine_type: List of preferred cuisines
            
        Returns:
            Updated user profile dict
        """
        if restrictions is None:
            restrictions = []
        if diet_type is None:
            diet_type = []
        if cuisine_type is None:
            cuisine_type = []
        
        # Filter out "None" from lists
        restrictions = [r for r in restrictions if r != "None"]
        diet_type = [d for d in diet_type if d != "None"]
        
        update_data = {
            'full_name': full_name,
            'birth_date': birth_date,
            'gender': gender if gender else None,
            'household_number': household_number,
            'restrictions': restrictions,
            'diet_type': diet_type,
            'cuisine_type': cuisine_type,
        }
        
        try:
            response = self.client.table('users').update(update_data).eq('user_id', self.user_id).execute()
            if response.data:
                return response.data[0]
            raise Exception("No data returned from update")
        except Exception as e:
            raise Exception(f"Failed to update profile: {str(e)}")
