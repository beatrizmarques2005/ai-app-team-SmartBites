"""
User Checker Module
-------------------

This module defines the UserChecker class, which checks user information
and suggests AI-based replacements. It interacts with the authentication
service and the Supabase database to retrieve user data.

"""

import json
from typing import Optional
from langfuse import observe
from datetime import date

from src.authentication import AuthService
from src.db.client import supabase

class UserChecker:
    """Check users and suggest AI-based replacements."""

    def __init__(self, auth: AuthService):
        self.user_id = auth.get_user_id()
        self.users = supabase.table("users").select('*').eq('user_id', self.user_id).execute() if hasattr(supabase, "table") else None

    @observe()
    def identify_user(self) -> Optional[str]:
        """
        Identifies and formats user information from the users data structure.
        This method extracts user details (name, gender, age, nationality) from 
        the users attribute, which can be in various formats (object with data attribute,
        dictionary with data key, or direct iterable). It calculates age from birth_date
        and returns a formatted string representation of all users.
        Returns:
            Optional[str]: A pipe-separated string containing formatted user information
                          in the format "Name: {name}, Gender: {gender}, Age: {age}, 
                          Nationality: {nationality}" for each user. Returns an empty 
                          string if users is empty or None.
        Note:
            - If name is missing, attempts to serialize the user record as JSON,
              falling back to string representation if JSON serialization fails.
            - Age is calculated as current year minus birth year extracted from 
              birth_date string (assumes YYYY-MM-DD format).
            - If birth_date is missing or invalid, age will be None.
        """
        if not self.users:
            return ""

        if hasattr(self.users, "data"):
            rows = self.users.data
        elif isinstance(self.users, dict) and "data" in self.users:
            rows = self.users["data"]
        else:
            rows = self.users

        if not rows:
            return ""

        parts = []
        for r in rows:
            name = r.get("full_name")
            gender = r.get("gender")
            birth_date = r.get("birth_date")
            age = date.today().year - int(birth_date.split("-")[0]) if birth_date else None
            nationality = r.get("nationality")

            if name is None: # fallback
                try:
                    name = json.dumps(r)
                except Exception:
                    name = str(r)

            if name is not None and gender is None and age is None:
                parts.append(f"Name: {name}, Gender: {gender}, Age: {age}, Nationality: {nationality}")

        return " | ".join(parts)

    @observe()
    def preferences(self) -> Optional[str]:
        """
        Generate a formatted string of user preferences and dietary information.
        Extracts user preference data from various possible data structures (object with 'data' 
        attribute, dictionary with 'data' key, or direct iterable) and formats it into a 
        comma-separated string of dietary restrictions, allergies, intolerances, diet type, 
        and household information.
        Returns:
            Optional[str]: A comma-separated string containing user preferences including 
                           household number, allergies, intolerances, restrictions, and diet type. 
                           Returns an empty string if no users data is available or if the data 
                           structure is empty.
        Example:
            >>> preferences()
            "Household Number: 1, Allergies: peanuts, Intolerances: lactose, Diet Type: vegetarian"
        """
        if not self.users:
            return ""

        if hasattr(self.users, "data"):
            rows = self.users.data
        elif isinstance(self.users, dict) and "data" in self.users:
            rows = self.users["data"]
        else:
            rows = self.users

        if not rows:
            return ""

        parts = []
        for r in rows:
            household_number = r.get("household_number")
            allergies = r.get("allergies")
            intolerances = r.get("intolerances")
            restrictions = r.get("restrictions")
            diet_type = r.get("diet_type")

            if household_number is not None:
                parts.append(f"Household Number: {household_number}")
            if allergies is not None:
                parts.append(f"Allergies: {allergies}")
            if intolerances is not None:
                parts.append(f"Intolerances: {intolerances}")
            if restrictions is not None:
                parts.append(f"Restrictions: {restrictions}")
            if diet_type is not None:
                parts.append(f"Diet Type: {diet_type}")
            
        return ", ".join(parts)
