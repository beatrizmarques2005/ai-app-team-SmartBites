'''
AI Client Module
-----------------

« description of the file »
'''

# =========================================================
# Imports
# =========================================================

import os
from dotenv import load_dotenv
import google.generativeai as genai

# =========================================================
# AI Client Class
# =========================================================
class AIClient:
    """Simple client for Google Gemini API"""
    
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def chat(self, message):
        try:
            response = self.model.generate_content(message)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def chat_with_history(self, messages):
        """Chat with conversation history (list of messages)"""
        try:
            chat = self.model.start_chat(history=[])
            response = chat.send_message(messages[-1])  # Send latest message
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"