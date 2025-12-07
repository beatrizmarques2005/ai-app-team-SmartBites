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

        self.model = os.getenv("MODEL") or "gemini-1.5-flash"
        self.temperature = float(os.getenv("TEMPERATURE") or 0.7)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        print("AIService base_dir =", base_dir) 

        file_path = os.path.join(base_dir, "system_instruction.txt")
        print("Looking for system_instruction.txt at:", file_path)  

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
            response = requests.get(url, timeout=30)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            # Use BeautifulSoup to get clean text from the HTML, which is better for the model
            soup = BeautifulSoup(response.content, 'html.parser')
            # Return a max of 4000 characters of clean text to avoid hitting context limits
            return soup.get_text()[:4000]
        except requests.exceptions.RequestException as e:
            return f"Error fetching URL content: {e}"

    def create_chat(self, auth: AuthService):
        """Create a new chat session."""
        ingredientchecker = PantryChecker(auth)
        userchecker = UserChecker(auth)
        pantrywriter = PantryWriter(auth)
        recipewriter = RecipeWriter(auth)
        shoppingwriter = ShoppingListWriter(auth)
        recipechecker = RecipeChecker(auth)

        return self.client.chats.create(
                    model=self.model,
                    config = {
                        'temperature': self.temperature,
                        'max_output_tokens': int(os.getenv("MAX_OUTPUT_TOKENS")),
                        'system_instruction': str(self.system_instruction), 
                        'tools' : [self.fetch_url_content, 
                                   ingredientchecker.available_ingredients,
                                   userchecker.identify_user,
                                   userchecker.preferences,
                                   pantrywriter.add_items,
                                   recipewriter.add_recipes,
                                   shoppingwriter.add_shopping_items,
                                   recipechecker.recent_recipes,
                                   ]
                    }, 
        )

    def send_message(self, chat, prompt: str):
        """Send a message to an existing chat."""
        return chat.send_message(prompt)
