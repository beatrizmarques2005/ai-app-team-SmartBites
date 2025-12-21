"""
AI Service - Consolidated AI helpers for the application

This file merges extraction, recipe generation, recipe QA and flavor-suggestion
helpers into a single service to avoid scattering AI logic across multiple files.
"""
import json
import os
from pathlib import Path
from io import BytesIO
from datetime import datetime

import google.genai as genai
from google.genai import types
from dotenv import load_dotenv
from langfuse import observe
import time
from google.api_core.exceptions import ServiceUnavailable

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
    
    @observe()
    def extract_structured(self, file_bytes: bytes, schema: dict, mime_type: str) -> dict:
        """
        Extract structured receipt data directly using Gemini's multimodal API.
        Does NOT create a chat — just calls the AI model with the file.
        """
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
                    max_output_tokens=8000  # Increased to 8000 to ensure enough tokens
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

    @observe()
    def web_search(self, query: str) -> dict:
        """Search the web for recipes using trusted sources."""

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
    def save_research_note(self, topic: str, summary: str) -> dict:
        """Save a research note."""
        print(f"[Saved note: {topic}]")
        return {"status": "saved", "topic": topic}
    
    @observe()
    def create_chat(self, auth: AuthService):

        # Get the current date and time
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        # Append the date to your system instruction
        dynamic_instruction = (
            f"Current Date: {current_date}\n\n"
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
            # add_shopping_items_llm,
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


                return "I'm processing that for you, one moment..."

            except Exception as e:
                if "503" in str(e) or "ServiceUnavailable" in str(e):
                    wait_time = 2 ** attempt
                    print(f"[Gemini overloaded] Retry {attempt + 1}/{max_retries} in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                print(f"Error during send_message: {e}")
                return f"I encountered an error: {e}"

        return "🚦 SmartBites is currently busy. Please try again in a minute."

