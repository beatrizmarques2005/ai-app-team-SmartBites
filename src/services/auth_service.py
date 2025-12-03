import os
from src.db.client import supabase

class AuthService:
    def __init__(self):
        self.client = supabase

    def signup(self, email: str, password: str, username: str = None):
        """Register a new user using Supabase Auth."""
        resp = self.client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "username": username
                }
            }
        })
        return resp

    def login(self, email: str, password: str):
        """Login a user and return the auth session."""
        resp = self.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return resp

    def logout(self):
        """Invalidate the current session."""
        return self.client.auth.sign_out()