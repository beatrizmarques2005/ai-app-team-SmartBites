"""
AI Service - Consolidated AI helpers for the application

This file merges extraction, recipe generation, recipe QA and flavor-suggestion
helpers into a single service to avoid scattering AI logic across multiple files.
"""

import os
# import json
# import tempfile
# import re
from typing import Optional, Any

import google.genai as genai
from google.genai.types import Part
# from google.genai.errors import APIError
# from google.genai.types import GenerationConfig
from dotenv import load_dotenv
# from langfuse import observe
import requests
from bs4 import BeautifulSoup
#from utils.prompts import PromptLoader

load_dotenv()

class AIService:
    """Service for all AI operations using Gemini."""

    def __init__(self):
        """Initialize AI service.

        Args:
            api_key: Optional API key for the generative API. If omitted, `GOOGLE_API_KEY` env var is used.
            model_name: Optional model name. If omitted, `MODEL` env var is used.
            temperature: Optional temperature (float). If omitted, `TEMPERATURE` env var or 0.7 is used.
        """

        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        self.model = os.getenv("MODEL") or "gemini-1.5-flash"
        self.temperature = float(os.getenv("TEMPERATURE") or 0.7)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        print("AIService base_dir =", base_dir)  # DEBUG

        file_path = os.path.join(base_dir, "system_instruction.txt")
        print("Looking for system_instruction.txt at:", file_path)  # DEBUG

        with open(file_path, "r", encoding="utf-8") as file:
            self.system_instruction = file.read()


    # --- Tool Definition (Function Calling) ---
    def fetch_url_content(self, url: str) -> str:
        """
        Fetches the plaintext content of a specific public URL.
        Use this tool when the user provides a link and asks for a summary or details.

        Args:
            url: The complete URL (e.g., 'https://www.mysite.com/recipe') to fetch content from.
        
        Returns:
            The raw text content of the page, or a simple error message if inaccessible.
        """
        print(f"Executing Tool: fetch_url_content for {url}")
        try:
            # Simple request to fetch the content with a timeout
            response = requests.get(url, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            # Use BeautifulSoup to get clean text from the HTML, which is better for the model
            soup = BeautifulSoup(response.content, 'html.parser')
            # Return a max of 4000 characters of clean text to avoid hitting context limits
            return soup.get_text()[:4000]
        except requests.exceptions.RequestException as e:
            return f"Error fetching URL content: {e}"






    def create_chat(self):
        """Create a new chat session."""
        return self.client.chats.create(
                    model=self.model,
                    config = {
                        'temperature': self.temperature,
                        'max_output_tokens': int(os.getenv("MAX_OUTPUT_TOKENS")),
                        'system_instruction': str(self.system_instruction), 
                        'tools' : [self.fetch_url_content]

                    }, 

        )
        

    # def send_message(self, chat, message: str):
    #     """Send a message to an existing chat."""
    #     return chat.send_message(message)

    def send_message(self, chat, prompt: str):
        """Send a message to an existing chat, handling potential tool calls."""
        
        response = chat.send_message(prompt)
        
        # Helper function to extract tool calls from the response
        def get_function_calls(res):
            if res.candidates and res.candidates[0].content:
                # Iterate through parts and find those that contain function calls
                return [part.function_call for part in res.candidates[0].content.parts 
                        if part.function_call]
            return []

        # 1. Loop until the model returns a final text response (i.e., no more tool calls)
        function_calls = get_function_calls(response)
        
        # Check for function calls using the correct content structure
        while function_calls:
            tool_responses = []

            for tool_call in function_calls:
                # The model uses the function_call object directly here
                function_name = tool_call.name
                function_args = dict(tool_call.args)

                # 2. Execute the specific tool function
                if function_name == 'fetch_url_content':
                    # Call the actual Python function with the model's arguments
                    content = self.fetch_url_content(**function_args)
                    
                    # 3. Format the result to send back to the model
                    tool_responses.append(Part.from_tool_response(
                        name=function_name,
                        response=content
                    ))
                else:
                    # Handle unknown tool call (shouldn't happen with our setup)
                    tool_responses.append(Part.from_tool_response(
                        name=function_name,
                        response=f"Error: Unknown tool {function_name}"
                    ))
                
            # 4. Send the tool output back to the model with the role set to 'tool'
            # FIX: Wrapping the parts in a Content object with the role set to 'tool'
            tool_content = Content(role='tool', parts=tool_responses)
            response = chat.send_message(contents=[tool_content])
            
            # Update the function_calls list for the next iteration
            function_calls = get_function_calls(response)

        return response # The final text response