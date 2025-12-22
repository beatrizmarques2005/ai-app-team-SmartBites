"""
Authentication Module
---------------------

This module handles user authentication using Supabase Auth.

"""
from langfuse import observe
from src.db.client import supabase

class AuthService:
    def __init__(self):
        self.client = supabase
        self.user = None

    @observe()
    def signup(self, email: str, password: str, username: str = None):
        """
        Register a new user with email and password.
        
        Args:
            email (str): The email address of the user to register.
            password (str): The password for the user account.
            username (str, optional): The username for the user profile. Defaults to None.
        
        Returns:
            The authentication response object containing user details and session information.
        
        Raises:
            AuthError: If the signup fails due to invalid credentials or existing email.
        """
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

    @observe()
    def login(self, email: str, password: str):
        """
        Authenticate a user by signing in with email and password.
        
        Args:
            email (str): The user's email address.
            password (str): The user's password.
        
        Returns:
            The authentication response object containing user credentials and session information.
        
        Raises:
            AuthError: If the email or password is invalid.
        """
        resp = self.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        self.user = resp.user
        return resp
    
    @observe()
    def get_user_id(self):
        """
        Retrieve the user ID from the current user object.
        
        Returns:
            int or None: The ID of the authenticated user if a user is logged in,
                         otherwise returns None.
        """
        return self.user.id if self.user else None

    @observe()
    def logout(self):
        """
        Sign out the currently authenticated user.
        
        This method terminates the user's session by calling the authentication
        client's sign_out method.
        
        Returns:
            The response from the authentication service after signing out.
        
        Raises:
            Exception: If the sign_out operation fails or the user is not authenticated.
        """
        return self.client.auth.sign_out()
