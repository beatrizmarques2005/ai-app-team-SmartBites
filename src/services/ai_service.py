"""
AI Service
----------

Consolidated AI helpers for the application

This file merges extraction, recipe suggestion, recipe QA and flavor-suggestion
helpers into a single service to avoid scattering AI logic across multiple files.

"""
import json
import os
import logging
from pathlib import Path
from datetime import datetime

import google.genai as genai
from google.genai import types
from dotenv import load_dotenv
from langfuse import observe
import time

from src.authentication import AuthService
from src.tools.pantry_checker import PantryChecker
from src.tools.user_checker import UserChecker
from src.tools.pantry_writer import PantryWriter
from src.tools.recipe_writer import RecipeWriter
from src.tools.recipe_checker import RecipeChecker
from src.tools.shopping_writer import ShoppingListWriter
from src.tools.cooking_assistant import CookingAssistant
from src.utils.pending_meal_plan import PendingMealPlan
from src.utils.meal_plan_flow import handle_meal_plan_flow

load_dotenv()

class AIService:
    """Service for all AI operations using Gemini."""

    def __init__(self):
        """Initialize AI service."""

        # env variables
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = os.getenv("MODEL")
        self.temperature = float(os.getenv("TEMPERATURE"))
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS"))

        # load system instruction from file
        base_dir = Path(__file__).resolve().parent
        file_path = base_dir / "system_instruction.txt"
        print(f"Searching in: {file_path}")

        if not file_path.exists():
            alt_path = base_dir.parent / "system_instruction.txt"
            if alt_path.exists():
                file_path = alt_path
                print(f"Found file in alternative path: {file_path}")
            else:
                raise FileNotFoundError(f"Could not find system_instruction.txt at {file_path}")

        with open(file_path, "r", encoding="utf-8-sig") as file:
            raw_data = file.read()
            print(f"DEBUG: Character count: {len(raw_data)}")
            print(f"DEBUG: Content starts with: {raw_data[:20]}")
            self.system_instruction = raw_data
    
    def _attempt_json_repair(self, json_text: str) -> str:
        """
        Attempt to repair incomplete JSON by adding missing closing braces.
        
        Args:
            json_text: Potentially incomplete JSON string
            
        Returns:
            Repaired JSON string
        """
        # Count opening and closing braces
        open_braces = json_text.count('{')
        close_braces = json_text.count('}')
        open_brackets = json_text.count('[')
        close_brackets = json_text.count(']')
        
        # If there are unclosed structures, try to close them
        repaired = json_text
        
        # Remove any trailing incomplete string (ends with unclosed quote)
        if repaired.rstrip().endswith(','):
            repaired = repaired.rstrip()[:-1]
        
        # Add missing closing brackets for arrays
        if open_brackets > close_brackets:
            repaired += ']' * (open_brackets - close_brackets)
        
        # Add missing closing braces for objects
        if open_braces > close_braces:
            repaired += '}' * (open_braces - close_braces)
        
        return repaired
    
    @observe()
    def extract_structured(self, file_bytes: bytes, schema: dict, mime_type: str) -> dict:
        """
        Extracts structured data from a given file in bytes format using a specified schema and MIME type.
        Args:
            file_bytes (bytes): The byte content of the file to be processed.
            schema (dict): A dictionary defining the schema for the structured data extraction.
            mime_type (str): The MIME type of the file (e.g., 'image/jpeg').
        Returns:
            dict: A dictionary containing the extracted structured data or an error message.
                  The structure of the returned dictionary is:
                  {
                      "items": [...],  # List of extracted items
                      "error": str     # Error message if extraction fails
                  }
        Raises:
            json.JSONDecodeError: If the response from the AI cannot be parsed as valid JSON.
            Exception: For any other errors that occur during the extraction process.
        """

        if mime_type == "image/jpg":
            mime_type = "image/jpeg"
        
        try:

            schema_prompt = f"""
                            You are a strict JSON generator.

                            Extract receipt data following EXACTLY this schema:
                            {json.dumps(schema, indent=2)}

                            CRITICAL RULES (MANDATORY):
                            - Output MUST be valid, COMPLETE JSON
                            - MUST end with proper closing braces
                            - Use double quotes for all keys and strings
                            - Escape special characters in strings (quotes, backslashes, newlines)
                            - Do NOT include trailing commas
                            - Do NOT include comments
                            - Do NOT include explanations or extra text
                            - Use null for missing values (not None)
                            - Output JSON only, no markdown, no backticks
                            - Keep string values concise to avoid token limits
                            - VERIFY the JSON is complete before finishing
                            """

            # sending file directly to Gemini via multimodal API
            # Use higher token limit to prevent truncation of large receipts
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
                    max_output_tokens=16384  # Increased to prevent truncation
                )
            )

            if response is None:
                return {"items": [], "error": "Gemini returned None response"}
            
            response_text = None
            
            # direct text attribute
            if hasattr(response, 'text') and response.text:
                response_text = response.text
            # try candidates array
            elif hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text = part.text
                                break
                    if response_text:
                        break
            
            # just for debug
            if response_text is None:
                finish_reason = "unknown"
                if hasattr(response, 'candidates') and response.candidates:
                    finish_reason = getattr(response.candidates[0], 'finish_reason', 'unknown')
                return {"items": [], "error": f"Gemini returned no text. Finish reason: {finish_reason}"}

            response_text = response_text.strip()
            if not response_text:
                return {"items": [], "error": "Gemini returned empty text (after stripping)"}
            
            if response_text.startswith("```json"):
                response_text = response_text[7:] 
            elif response_text.startswith("```"):
                response_text = response_text[3:] 
            
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            if not response_text.endswith('}'):
                logging.warning(f"Response may be incomplete. Length: {len(response_text)}")
                logging.warning(f"Last 100 chars: {response_text[-100:]}")
            
            try:
                structured_data = json.loads(response_text)
                return structured_data
            except json.JSONDecodeError as first_error:
                logging.warning(f"Initial JSON parse failed: {str(first_error)}")
                logging.warning("Attempting to repair JSON...")
                
                try:
                    repaired_text = self._attempt_json_repair(response_text)
                    structured_data = json.loads(repaired_text)
                    logging.info("Successfully repaired and parsed JSON")
                    return structured_data
                except json.JSONDecodeError:
                    raise first_error
        
        except json.JSONDecodeError as e:
            error_context = f"Character position: {e.pos if hasattr(e, 'pos') else 'unknown'}"
            preview_start = max(0, (e.pos if hasattr(e, 'pos') else 500) - 200)
            preview_end = min(len(response_text) if response_text else 0, preview_start + 400)
            text_preview = response_text[preview_start:preview_end] if response_text else 'EMPTY'
            
            logging.error(f"JSON Parse Error: {str(e)}")
            logging.error(f"Full response length: {len(response_text) if response_text else 0}")
            logging.error(f"Context around error: {text_preview}")
            
            return {
                "items": [], 
                "error": f"Failed to parse AI output as JSON: {str(e)}. {error_context}. Response length: {len(response_text) if response_text else 0}. Context: ...{text_preview}..."
            }
        except Exception as e:
            import traceback
            logging.error(f"Unexpected error in extract_structured: {str(e)}")
            logging.error(traceback.format_exc())
            return {"items": [], "error": f"Error: {str(e)}\n{traceback.format_exc()}"}

    @observe()
    def web_search(self, query: str) -> dict:
        """
        Perform a web search using trusted sources to find relevant information based on the provided query.
        This method constructs a search query that filters results to a predefined list of trusted sources. 
        It then sends the query to a content generation model and retrieves the results. If any verified sources 
        are found, it appends their titles and URIs to the response.
        Args:
            query (str): The search query string to be used for the web search.
        Returns:
            dict: A dictionary containing the generated answer and a list of verified sources found during the search.
                The structure of the dictionary is:
                {
                    "answer": str,  # The generated answer from the model
                    "sources": list  # List of verified sources found
                }
        """

        trusted_sources = [
            "tudogostoso.com.br", "feed.continente.pt", "auchaneeu.auchan.pt",
            "pingodoce.pt", "receitaslidl.pt", "allrecipes.com",
            "simplehomeedit.com", "pinchofyum.com", "alisoneroman.com", 
            "bbcgoodfood.com"
        ]
        
        site_filter = " OR ".join([f"site:{site}" for site in trusted_sources])
        full_query = f"{query} ({site_filter})"

        print(f"[Searching Trusted Sources: {query}]")

        response = self.client.models.generate_content(
            model=self.model,
            contents=full_query,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.0,
            )
        )

        source_text = "\n\nVERIFIED SOURCES FOUND:"
        if response.candidates and len(response.candidates) > 0:
            metadata = response.candidates[0].grounding_metadata
            if metadata and hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                for chunk in metadata.grounding_chunks:
                    source_text += f"\n- {chunk.web.title}: {chunk.web.uri}"
        
        return {"answer": response.text + source_text}

    @observe()
    def save_research_note(self, topic: str) -> dict:
        """
        Save a research note for a given topic.

        Args:
            topic (str): The topic of the research note to be saved.

        Returns:
            dict: A dictionary containing the save status and the topic.
                - "status" (str): The status of the save operation (e.g., "saved").
                - "topic" (str): The topic that was saved.

        Example:
            >>> result = save_research_note("Machine Learning")
            >>> print(result)
            {'status': 'saved', 'topic': 'Machine Learning'}
        """
        print(f"[Saved note: {topic}]")
        return {"status": "saved", "topic": topic}
    
    @observe()
    def create_chat(self, auth: AuthService):
        """
        Creates a chat session with configured tools and system instructions for the AI assistant.
        This method initializes a new chat instance with multiple tool integrations for managing
        recipes, pantry items, user preferences, and shopping lists. It enriches the system
        instruction with the current date to enable temporal reasoning.
        Args:
            auth (AuthService): Authentication service instance used to initialize various
                               checker and writer tools for database operations.
        Returns:
            Chat: A configured chat session object with:
                - Tools for pantry management, recipe management, user preferences, and cooking assistance
                - Dynamic system instructions including current date
                - Configured temperature and token limit settings
                - An attached PendingMealPlan instance for tracking meal planning state
        Tools included:
            - Web search and research note saving
            - Ingredient availability checking
            - User identification and preference retrieval
            - Pantry item management (add/update)
            - Recipe management (add/retrieve)
            - Shopping list management (add/remove items)
            - Cooking assistance and advice
        """

        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        dynamic_instruction = (
            f"Current Date: {current_date}\n\n" # add today's date to system instruction so LLM can reason about weekdays
            f"{self.system_instruction}"
        )

        ingredientchecker = PantryChecker(auth)
        userchecker = UserChecker(auth)
        pantrywriter = PantryWriter(auth)
        recipewriter = RecipeWriter(auth)
        recipechecker = RecipeChecker(auth)
        shoppingwriter = ShoppingListWriter(auth)
        cooking_assistant = CookingAssistant()

        tools = [
            self.web_search,
            self.save_research_note,
            ingredientchecker.available_ingredients,
            userchecker.identify_user,
            userchecker.preferences,
            pantrywriter.add_items,
            recipewriter.add_recipes,
            shoppingwriter.add_shopping_items,
            shoppingwriter.remove_item,
            recipechecker.recent_recipe_names,
            cooking_assistant.advise,
        ]

        config = types.GenerateContentConfig(
            tools=tools,
            system_instruction=dynamic_instruction,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
        )

        chat = self.client.chats.create(model=self.model, config=config)
        chat.pending_meal_plan = PendingMealPlan()
        return chat

    @observe()
    def send_message(self, chat, prompt: str, max_retries: int = 3):
        """
        Send a message to the AI chat and retrieve a response with retry logic.
        Handles meal plan flows if applicable, and implements exponential backoff
        retry logic for service unavailability errors.
        Args:
            chat: The chat object used to send messages and retrieve responses.
            prompt (str): The user's message or query to send to the AI.
            max_retries (int, optional): Maximum number of retry attempts for failed requests. Defaults to 3.
        Returns:
            str: The AI's response text. Returns status messages for special cases:
                - Processing message if no text is available but response exists
                - Error message if an exception occurs (non-503 errors)
                - Service busy message if max retries are exceeded
        Raises:
            None: All exceptions are caught and handled internally, returning error messages instead.
        Notes:
            - First checks for pending meal plans and delegates to handle_meal_plan_flow if applicable.
            - Implements exponential backoff (2^attempt seconds) for 503/ServiceUnavailable errors.
            - Attempts to extract text from response candidates if direct response.text is unavailable.
        """
        plan = getattr(chat, "pending_meal_plan", None)

        if plan and (plan.awaiting_approval or plan.meals):
            result = handle_meal_plan_flow(chat, prompt)
            if result is not None:
                return result

        for attempt in range(max_retries):
            try:
                response = chat.send_message(prompt)

                if response.text:
                    return response.text

                if response.candidates:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        return "".join([p.text for p in candidate.content.parts if getattr(p, "text", None)])
                    
                return "System Failed. Please upload your prompt again. We are sorry for the inconvenience"

            except Exception as e:
                if "503" in str(e) or "ServiceUnavailable" in str(e):
                    wait_time = 2 ** attempt
                    print(f"[Gemini overloaded] Retry {attempt + 1}/{max_retries} in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                print(f"Error during send_message: {e}")
                return f"I encountered an error: {e}"

        return "🚦 SmartBites is currently busy. Please try again in a minute."

