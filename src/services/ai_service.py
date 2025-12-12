"""
AI Service - Consolidated AI helpers for the application

This file merges extraction, recipe generation, recipe QA and flavor-suggestion
helpers into a single service to avoid scattering AI logic across multiple files.
"""
import requests
from bs4 import BeautifulSoup
import os
import google.genai as genai
from dotenv import load_dotenv
from google.genai import types

import json
from io import BytesIO
from PyPDF2 import PdfReader
from langfuse import observe

from src.tools.search import Search
from src.tools.pantry_checker import PantryChecker
from src.tools.user_checker import UserChecker
from src.tools.pantry_writer import PantryWriter
from src.tools.recipe_writer import RecipeWriter
from src.tools.recipe_checker import RecipeChecker
from src.tools.shopping_writer import ShoppingListWriter

from src.authentication import AuthService

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

        self.model = os.getenv("MODEL")
        self.temperature = float(os.getenv("TEMPERATURE"))
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS"))

        base_dir = os.path.dirname(os.path.abspath(__file__))
        print("AIService base_dir =", base_dir) 

        file_path = os.path.join(base_dir, "system_instruction.txt")
        print("Looking for system_instruction.txt at:", file_path)  

        with open(file_path, "r", encoding="utf-8") as file:
            self.system_instruction = file.read()
        
        self.tool_registry = {}

    @observe()
    def extract_structured(self, file_bytes: bytes, schema: dict, mime_type: str) -> dict:
        """
        Extract structured receipt data directly using Gemini's multimodal API.
        Does NOT create a chat — just calls the AI model with the file.
        """
        # Normalize MIME type
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        try:
            # Create a very concise prompt to save tokens
            schema_prompt = f"""Extract receipt data as JSON:
                                {json.dumps(schema, indent=2)}
                                Return ONLY valid JSON."""

            # Send file directly to Gemini via multimodal API
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    schema_prompt,
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=mime_type
                    )
                ],
                config=genai.types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens,
                )
            )

            # Check if response exists
            if response is None:
                return {"items": [], "error": "Gemini returned None response"}
            
            # Try to extract text from response
            response_text = None
            
            # First try direct text attribute
            if hasattr(response, 'text') and response.text:
                response_text = response.text
            # If that fails, try candidates array
            elif hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text = part.text
                                break
                    if response_text:
                        break
            
            if response_text is None:
                # Get finish_reason from candidates for debugging
                finish_reason = "unknown"
                if hasattr(response, 'candidates') and response.candidates:
                    finish_reason = getattr(response.candidates[0], 'finish_reason', 'unknown')
                return {"items": [], "error": f"Gemini returned no text. Finish reason: {finish_reason}"}

            # Parse JSON response
            response_text = response_text.strip()
            if not response_text:
                return {"items": [], "error": "Gemini returned empty text (after stripping)"}
            
            # Remove markdown code block wrapping if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            elif response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove trailing ```
            
            response_text = response_text.strip()
            
            structured_data = json.loads(response_text)
            return structured_data

        except json.JSONDecodeError as e:
            # Return more diagnostic info about the failed text
            return {"items": [], "error": f"Failed to parse AI output as JSON: {str(e)}. Text preview: {response_text[:100] if response_text else 'EMPTY'}"}
        except Exception as e:
            import traceback
            return {"items": [], "error": f"Error: {str(e)}\n{traceback.format_exc()}"}
    
    ###############################
    ######### O NOSSO!!!! #########
    ###############################

    # # --- Tool Definition (Function Calling) ---
    # def fetch_url_content(self, url: str) -> str:
    #     """
    #     Fetches the plaintext content of a specific public URL.
    #     Use this tool when the user provides a link and asks for a summary or details.

    #     Args:
    #         url: The complete URL (e.g., 'https://www.mysite.com/recipe') to fetch content from.
        
    #     Returns:
    #         The raw text content of the page, or a simple error message if inaccessible.
    #     """
    #     print(f"Executing Tool: fetch_url_content for {url}")
    #     try:
    #         # Simple request to fetch the content with a timeout
    #         response = requests.get(url, timeout=30)
    #         response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
    #         # Use BeautifulSoup to get clean text from the HTML, which is better for the model
    #         soup = BeautifulSoup(response.content, 'html.parser')
    #         # Return a max of 4000 characters of clean text to avoid hitting context limits
    #         return soup.get_text()[:4000]
    #     except requests.exceptions.RequestException as e:
    #         return f"Error fetching URL content: {e}"

    # def create_chat(self, auth: AuthService):
    #     """Create a new chat session."""
    #     ingredientchecker = PantryChecker(auth)
    #     userchecker = UserChecker(auth)
    #     pantrywriter = PantryWriter(auth)
    #     recipewriter = RecipeWriter(auth)
    #     shoppingwriter = ShoppingListWriter(auth)
    #     recipechecker = RecipeChecker(auth)

    #     return self.client.chats.create(
    #                 model=self.model,
    #                 config = {
    #                     'temperature': self.temperature,
    #                     'max_output_tokens': int(self.max_output_tokens),
    #                     'system_instruction': str(self.system_instruction), 
    #                     'tools' : [
    #                         # self.fetch_url_content, 
    #                                ingredientchecker.available_ingredients,
    #                                userchecker.identify_user,
    #                                userchecker.preferences,
    #                                pantrywriter.add_items,
    #                                recipewriter.add_recipes,
    #                                shoppingwriter.add_shopping_items,
    #                                recipechecker.recent_recipes,
    #                                ]
    #                 }, 
    #     )
    
    def create_chat(self, auth: AuthService):
        ingredientchecker = PantryChecker(auth)
        userchecker = UserChecker(auth)
        pantrywriter = PantryWriter(auth)
        recipewriter = RecipeWriter(auth)
        recipechecker = RecipeChecker(auth)
        shoppingwriter = ShoppingListWriter(auth)
        search_tool = Search()

        # Define tools as JSON schemas (no callables)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "available_ingredients",
                    "description": "Check user's pantry ingredients",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "identify_user",
                    "description": "Identify the user",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "preferences",
                    "description": "Get user preferences",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "add_items",
                    "description": "Add items to pantry",
                    "parameters": {
                        "type": "object",
                        "properties": {"items": {"type": "array", "items": {"type": "string"}}},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search recipes or fetch URL content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipe_name": {"type": "string"},
                            "query": {"type": "string"},
                            "urls": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
        ]

        # Map tool names to your actual Python functions
        self.tool_registry = {
            "available_ingredients": ingredientchecker.available_ingredients,
            "identify_user": userchecker.identify_user,
            "preferences": userchecker.preferences,
            "add_items": pantrywriter.add_items,
            "add_recipes": recipewriter.add_recipes,
            "add_shopping_items": shoppingwriter.add_shopping_items,
            "recent_recipes": recipechecker.recent_recipes,
            "search": search_tool.run,
        }

        # Create chat (AI only sees schemas)
        return self.client.chats.create(
            model=self.model,
            config={
                "temperature": self.temperature,
                "max_output_tokens": int(self.max_output_tokens),
                "system_instruction": str(self.system_instruction),
                "tools": tools,  # JSON schemas only
            },
        )

    def send_message(self, chat, prompt: str):
        """Send a message to an existing chat."""
        return chat.send_message(prompt)
