
"""
AI Service - Consolidated AI helpers for the application

This file merges extraction, recipe generation, recipe QA and flavor-suggestion
helpers into a single service to avoid scattering AI logic across multiple files.
"""

import os
import json
import tempfile
import re
from typing import Optional, Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from dotenv import load_dotenv
from langfuse import observe
import requests
from bs4 import BeautifulSoup

load_dotenv()

class AIService:
    """Service for all AI/LLM operations."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, temperature: Optional[float] = None):
        """Initialize AI service.

        Args:
            api_key: Optional API key for the generative API. If omitted, `GOOGLE_API_KEY` env var is used.
            model_name: Optional model name. If omitted, `MODEL` env var is used.
            temperature: Optional temperature (float). If omitted, `TEMPERATURE` env var or 0.7 is used.
        """
        genai.configure(api_key=api_key or os.getenv("GOOGLE_API_KEY"))
        model_env = model_name or os.getenv("MODEL") or "gemini-1.5"
        self.model = genai.GenerativeModel(model_name=model_env)
        try:
            self.temperature = float(temperature if temperature is not None else os.getenv("TEMPERATURE", 0.7))
        except Exception:
            self.temperature = 0.7

    @observe()
    def extract_structured(self, file_bytes: bytes, schema: dict, mime_type: str = "application/pdf") -> dict:
        prompt = self._build_extraction_prompt(schema)

        # Write bytes to a temporary file
        suffix = ".pdf" if mime_type == "application/pdf" else ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_file_path = tmp_file.name

        # Upload the file using its path
        file_part = genai.upload_file(path=tmp_file_path, mime_type=mime_type)

        # Generate content with Gemini
        response = self.model.generate_content(
            contents=[prompt, file_part],
            generation_config=GenerationConfig(response_mime_type="application/json", temperature=self.temperature),
        )

        # Check for empty or invalid response
        if not getattr(response, "text", None) or response.text.strip() == "":
            raise ValueError("Gemini returned an empty response. The file may be unclear or the schema too strict.")

        raw_text = response.text.strip()

        # Remove Markdown-style code block if present
        if raw_text.startswith("```json") or raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.DOTALL).strip()

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Gemini returned invalid JSON: {raw_text}") from e

    @observe()
    def chat_with_context(self, question: str, context: dict, system_instruction: Optional[str] = None) -> str:
        """Chat with AI about specific context."""
        if system_instruction is None:
            system_instruction = "You are a helpful AI assistant analyzing data."

        chat = self.model.start_chat()
        chat.send_message(f"""{system_instruction}\nContext data:\n{json.dumps(context, indent=2)}""")
        response = chat.send_message(question)
        return response.text

    @observe()
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """Summarize text."""
        response = self.model.generate_content(contents=f"Summarize this in {max_sentences} sentences or less:\n\n{text}")
        return response.text

    @observe()
    def _build_extraction_prompt(self, schema: dict) -> str:
        """Build prompt for structured extraction."""
        return f"""Extract information from this document as JSON.

                Schema (use these exact field names):
                {json.dumps(schema, indent=2)}

                Rules:
                - Return ONLY valid JSON
                - Use null for missing information
                - Follow the exact field names
                - Match the data types specified

                JSON:"""

    @observe()
    def extract_recipe(self, html: str) -> Optional[dict]:
        """Extract structured recipe from HTML using the model."""
        prompt = f"""
        Extract a structured cooking recipe from the HTML below. 
        Only return valid JSON.

        Required JSON fields:
        - title: string
        - ingredients: list of strings
        - instructions: list of strings
        - estimated_time: integer (minutes)

        HTML:
        {html}
        """

        response = self.model.generate_content(
            contents=prompt,
            generation_config=GenerationConfig(temperature=self.temperature, response_mime_type="application/json"),
        )

        if not response or not getattr(response, "text", None):
            return None

        try:
            return json.loads(response.text)
        except Exception:
            return None

    @observe()
    def extract_recipe_from_html(self, html: str) -> Optional[dict]:
        """Backward-compatible alias: extract a recipe from raw HTML using the model."""
        # reuse extract_recipe implementation
        return self.extract_recipe(html)

    @observe()
    def get_recipe_links(self) -> list[str]:
        """Collect recipe links from configured RECIPE_SOURCES environment variable."""
        # Prefer RECIPES_SOURCES (new name), then RECIPES_SOURCE, then RECIPE_SOURCES
        sources_env = os.getenv("RECIPES_SOURCES") or os.getenv("RECIPES_SOURCE") or os.getenv("RECIPE_SOURCES")

        if not sources_env:
            # fallback: try reading .env in repository root for array-style values
            try:
                from pathlib import Path
                import re
                repo_root = Path(__file__).resolve().parents[2]
                env_path = repo_root / '.env'
                if env_path.exists():
                    text = env_path.read_text(encoding='utf-8')
                    m = re.search(r'RECIPES_SOURCES\s*=\s*\(([^)]*)\)', text, re.IGNORECASE | re.DOTALL)
                    if m:
                        sources_env = m.group(1)
                    else:
                        m2 = re.search(r'RECIPES_SOURCES\s*=\s*(.+)', text)
                        if m2:
                            sources_env = m2.group(1)
            except Exception:
                sources_env = None

        if sources_env:
            import re
            sources = re.findall(r"https?://[^\s\",)']+", sources_env)
        else:
            sources = []
        urls = []
        for site in sources:
            try:
                html = requests.get(site, timeout=5).text
            except requests.RequestException:
                continue
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(k in href for k in ["receita", "receitas", "recipe"]):
                    if href.startswith("http"):
                        urls.append(href)
                    else:
                        base = site.rstrip("/")
                        urls.append(base + "/" + href.lstrip("/"))
        return list(set(urls))

    @observe()
    def get_supermarket_recipes(self, max_recipes: int = 5) -> list[dict]:
        """Fetch and extract recipes from known recipe sources."""
        links = self.get_recipe_links()
        collected = []
        for link in links[:max_recipes]:
            try:
                html = requests.get(link, timeout=5).text
                recipe = self.extract_recipe_from_html(html)
                if recipe:
                    collected.append({"url": link, **recipe})
            except requests.RequestException:
                continue
        return collected

    @observe()
    def check_ingredients(self, recipe: dict, inventory_manager: Any) -> list[str]:
        """Check which ingredients from `recipe` are missing in the inventory manager."""
        try:
            available = inventory_manager.get_ingredients_for_recipe()
        except TypeError:
            # maybe requires user_id signature; try without args
            try:
                available = inventory_manager.get_ingredients_for_recipe()
            except Exception:
                available = []

        missing = []
        for item in recipe.get("ingredients", []):
            base = item.lower()
            found = False
            for inv in available:
                if inv.lower() in base:
                    found = True
                    break
            if not found:
                missing.append(item)
        return missing

    @observe()
    def get_possible_recipes(self, inventory_manager: Any) -> list[dict]:
        """Return possible recipes from supermarket sources that match the inventory."""
        supermarket_recipes = self.get_supermarket_recipes(max_recipes=10)
        possible = []
        for recipe in supermarket_recipes:
            missing = self.check_ingredients(recipe, inventory_manager)
            if len(missing) == 0:
                possible.append(recipe)
            else:
                recipe["missing_ingredients"] = missing
        return possible

    @observe()
    def generate_recipe_from_ingredients(self, ingredients: list[str], servings: int = 1, dietary: Optional[str] = None) -> Optional[dict]:
        """Generate a cooking recipe from given ingredients."""
        prompt = f"""
        Create a detailed cooking recipe using ONLY these ingredients:
        {', '.join(ingredients)}

        Requirements:
        - Prioritize ingredients close to expiration.
        - Adjust quantities for {servings} servings.
        """

        if dietary:
            prompt += f"\n- Make it suitable for a {dietary} diet."

        prompt += """
        Return only valid JSON with the structure:
        {
            "title": "...",
            "servings": int,
            "ingredients": [
                "ingredient - quantity"
            ],
            "instructions": [
                "step1", "step2", ...
            ]
        }
        """

        response = self.model.generate_content(
            contents=prompt,
            generation_config=GenerationConfig(temperature=self.temperature, response_mime_type="application/json"),
        )

        if not response or not getattr(response, "text", None):
            return None

        try:
            return json.loads(response.text)
        except Exception:
            return None

    @observe()
    def ask_recipe_question(self, recipe: dict, question: str) -> Optional[str]:
        """Ask the model a question about a recipe."""
        prompt = f"""
        You are a cooking assistant.

        Recipe:
        {json.dumps(recipe, indent=2)}

        Question:
        {question}
        """

        response = self.model.generate_content(contents=prompt, generation_config=GenerationConfig(temperature=self.temperature))
        return response.text if response else None

    @observe()
    def validate_recipe(self, data: dict) -> dict:
        """Ensure recipe contains required fields and normalize common keys."""
        return {
            "title": data.get("title"),
            "ingredients": data.get("ingredients", []),
            "instructions": data.get("instructions", []),
            "estimated_time_minutes": data.get("estimated_time") or data.get("estimated_time_minutes")
        }

    @observe()
    def suggestion(self, ingredients: list[str]) -> list[str]:
        """Suggest flavor enhancers (spices, herbs, condiments) for ingredients.

        Returns a list of suggestion strings. Attempts to parse JSON array; falls back to comma-split.
        """
        prompt = f"""
        You are a culinary AI assistant.
        Suggest spices, herbs, juices, or condiments to enhance the flavor of these ingredients: {', '.join(ingredients)}.
        Return the result as a JSON array of strings.
        """
        response = self.model.generate_content(contents=prompt, generation_config=GenerationConfig(temperature=self.temperature))
        try:
            return json.loads(response.text)
        except Exception:
            if not response or not getattr(response, "text", None):
                return []
            return [r.strip() for r in response.text.split(",") if r.strip()]

    @observe()
    def answer_question(self, question: str, context: dict, system_instruction: Optional[str] = None) -> str:
        """Generic QA helper that answers a question given a context dictionary.

        This centralizes AI-driven Q&A so callers (e.g., receipt flows, chat UI)
        can use a single API surface.
        """
        if system_instruction is None:
            system_instruction = "You are a helpful AI assistant analyzing provided context. Answer questions based only on the context; if information is missing, say so."
        return self.chat_with_context(question, context, system_instruction)

    @observe()
    def generate_recipe(self, inventory_manager: Any, servings: int = 1, dietary: Optional[str] = None):
        """Generate a recipe using an InventoryTool-like manager.

        `inventory_manager` must implement `get_ingredients_for_recipe()`.
        Returns a dict (parsed JSON) or an error string on failure.
        """
        try:
            ingredients = inventory_manager.get_ingredients_for_recipe()
        except Exception:
            return "Error: inventory manager does not provide `get_ingredients_for_recipe()`"

        if not ingredients:
            return "No available ingredients to elaborate a recipe."

        prompt = (
            f"Create a detailed recipe using these ingredients: {', '.join(ingredients)}\n"
            f"Prioritize ingredients that are close to their expiration date.\n"
            f"Adjust quantities for {servings} serving(s).\n"
        )

        if dietary:
            prompt += f"Make it suitable and safe for a {dietary} diet.\n"

        prompt += (
            "Return the recipe as JSON with keys: title, servings (int), ingredients (list of strings with quantities), "
            "instructions (list of steps)."
        )

        response = self.model.generate_content(
            contents=prompt,
            generation_config=GenerationConfig(temperature=self.temperature, response_mime_type="application/json"),
        )

        if not response or not getattr(response, "text", None):
            return "Error: empty response from model"

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return "Error: Unable to parse recipe JSON from model response."

    @observe()
    def cooking_advice(self, question: str, *, recipe: Optional[dict] = None, ingredients: Optional[list] = None, context: Optional[dict] = None) -> str:
        """Unified cooking helper.

        Usage patterns:
        - If `recipe` is provided, the question is interpreted as a question about that recipe and
          routed to `ask_recipe_question`.
        - If `ingredients` is provided and the question asks for suggestions (flavouring, substitutions),
          it routes to `suggestion` or `generate_recipe_from_ingredients` depending on the request.
        - Otherwise falls back to a generic QA using `answer_question` with an optional `context`.

        Returns a text answer (string). If a structured response is expected (e.g., recipe JSON), callers
        should call the more specific methods directly (`generate_recipe_from_ingredients`, `generate_recipe`, etc.).
        """

        # Prefer recipe-specific questions
        if recipe:
            resp = self.ask_recipe_question(recipe, question)
            return resp or "I couldn't find an answer about that recipe."

        # If ingredients are provided and the question mentions 'suggest' or 'substitute', offer suggestions
        if ingredients:
            q_lower = question.lower()
            if any(k in q_lower for k in ["suggest", "pair", "enhance", "flavor", "flavour"]):
                suggestions = self.suggestion(ingredients)
                if suggestions:
                    return "; ".join(suggestions)
                return "I couldn't generate suggestions for those ingredients."

            if any(k in q_lower for k in ["make", "recipe", "cook", "create"]):
                # attempt to produce a recipe JSON and return a brief summary
                recipe_json = self.generate_recipe_from_ingredients(ingredients)
                if isinstance(recipe_json, dict):
                    title = recipe_json.get("title", "Untitled recipe")
                    servings = recipe_json.get("servings")
                    return f"Generated recipe: {title}" + (f" ({servings} servings)" if servings else "")
                return "I couldn't generate a recipe from those ingredients."

        # Fallback to generic QA with any provided context
        ctx = context or {}
        return self.answer_question(question, ctx)