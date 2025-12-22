"""
User Writer Module
------------------

This module provides functionality to update user profiles in the database.

"""

from typing import Dict, Any, Optional
from langfuse import observe

from ..db.client import supabase
from ..authentication import AuthService

class UserWriter:
    
    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        if not self.user_id:
            raise ValueError("User must be authenticated.")
        self.client = supabase
    
    @observe()
    def update_user_profile(
        self, 
        full_name: str,
        birth_date: Optional[str] = None,
        gender: Optional[str] = None,
        household_number: int = 1,
        restrictions: list = None,
        diet_type: list = None,
        cuisine_type: list = None,
        nationality: Optional[str] = None,
    ) -> Dict[str, Any]:
        
        """
        Update the user profile with provided information.
        Args:
            full_name (str): The full name of the user. Required.
            birth_date (Optional[str]): The birth date of the user in string format. Defaults to None.
            gender (Optional[str]): The gender of the user. Defaults to None.
            household_number (int): The number of people in the household. Defaults to 1.
            restrictions (list): A list of dietary restrictions for the user. Defaults to empty list.
            diet_type (list): A list of diet types preferred by the user. Defaults to empty list.
            cuisine_type (list): A list of cuisine types preferred by the user. Defaults to empty list.
            nationality (Optional[str]): The nationality of the user. Defaults to None.
        Returns:
            Dict[str, Any]: The updated user profile data as a dictionary.
        Raises:
            Exception: If the update operation fails or no data is returned from the database.
        """
        
        if restrictions is None:
            restrictions = []
        if diet_type is None:
            diet_type = []
        if cuisine_type is None:
            cuisine_type = []
        
        update_data = {
            'full_name': full_name,
            'birth_date': birth_date,
            'gender': gender if gender else None,
            'household_number': household_number,
            'restrictions': restrictions,
            'diet_type': diet_type,
            'cuisine_type': cuisine_type,
            'nationality': nationality,
        }
        
        try:
            response = self.client.table('users').update(update_data).eq('user_id', self.user_id).execute()
            if response.data:
                return response.data[0]
            raise Exception("No data returned from update")
        except Exception as e:
            raise Exception(f"Failed to update profile: {str(e)}")
        