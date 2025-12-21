"""
AI Service - Consolidated AI helpers for the application

This file merges extraction, recipe generation, recipe QA and flavor-suggestion
helpers into a single service to avoid scattering AI logic across multiple files.
"""
import json
import os
from pathlib import Path
from io import BytesIO

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
        
        RECEIPT_EXTRACTION_RULES = """
        You are extracting structured data from a supermarket receipt.

        Rules:
        - For each item, determine whether it is edible.
        - Edible items are food or beverages intended for human consumption.
        - Non-edible items include cleaning products, hygiene items, household supplies,
        batteries, utensils, paper goods, and similar products.
        - If you are unsure whether an item is edible, set is_edible = false.
        - Every item MUST include an is_edible boolean.
        """

        try:
            schema_prompt = f"""Extract receipt data as JSON:
                                {json.dumps(schema, indent=2)}
                                Return ONLY valid JSON."""

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

            if response is None:
                return {"items": [], "error": "Gemini returned None response"}
            
            response_text = None
            
            if hasattr(response, 'text') and response.text:
                response_text = response.text
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
            
            structured_data = json.loads(response_text)
            return structured_data

        except json.JSONDecodeError as e:
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
            system_instruction=self.system_instruction,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
        )

        chat = self.client.chats.create(model=self.model, config=config)
        chat.pending_meal_plan = PendingMealPlan()
        return chat
    
    @observe()
    def send_message(self, chat, prompt: str, max_retries: int = 3):
        """Send a message and wait for the final text response."""
        
        plan = getattr(chat, "pending_meal_plan", None)

        if plan and (plan.awaiting_approval or plan.meals):
            result = handle_meal_plan_flow(chat, prompt)

            # If meal planner handled it, return immediately
            if result is not None:
                return result
        
        print(max_retries)
        for attempt in range(max_retries):
            try:
                response = chat.send_message(prompt)
        
                """ if response.text:
                    return response.text"""
        
                if hasattr(response, "candidates") and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, "content") and candidate.content and hasattr(candidate.content, "parts") and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, "text") and part.text:
                                    return part.text    

                return "I'm checking your ingredients and looking for recipes... ask me again in a moment!"

            except ServiceUnavailable:
                wait_time = 2 ** attempt
                print(
                    f"[Gemini overloaded] Retry {attempt + 1}/{max_retries} in {wait_time}s"
                )
                time.sleep(wait_time)

        return "🚦 SmartBites is currently busy. Please try again in a minute."
    
    # @observe()
    # def send_message(self, chat, prompt: str):
    #     """Send a message and wait for the final text response."""
    #     response = chat.send_message(prompt)
        
    #     if response.text:
    #         return response.text
            
    #     return "I'm sorry, I couldn't process that request. Could you try again?"