from src.db.client import supabase

class AuthService:
    def __init__(self):
        self.client = supabase
        self.user = None

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
        self.user = resp.user
        return resp
    
    def get_user_id(self):
        return self.user.id if self.user else None

    def logout(self):
        """Invalidate the current session."""
        return self.client.auth.sign_out()
