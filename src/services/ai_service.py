"""
AI Service - Handles all Gemini API interactions

"""

import os
import json
import tempfile
import re
import pathlib

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from dotenv import load_dotenv
from langfuse import observe

load_dotenv()

model = str(os.getenv("MODEL"))
temperature = float(os.getenv("TEMPERATURE"))

class AIService:
    """Service for all AI/LLM operations."""

    def __init__(self, model: str = model):
        """Initialize AI service.

        Args:
            model: Gemini model to use
        """
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model_name=model)

    @observe()
    def extract_structured(self, file_bytes: bytes, schema: dict, mime_type: str = 'application/pdf') -> dict:
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
            generation_config=GenerationConfig(
                response_mime_type='application/json',
                temperature=temperature,
            )
        )

        # Check for empty or invalid response
        if not response.text or response.text.strip() == "":
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
    def chat_with_context(
        self,
        question: str,
        context: dict,
        system_instruction: str = None
    ) -> str:
        """Chat with AI about specific context."""
        if system_instruction is None:
            system_instruction = "You are a helpful AI assistant analyzing data."

        # Start the chat
        chat = self.model.start_chat()

        # Send system instruction and context as the first message
        chat.send_message(f"""{system_instruction}
                                Context data:
                                {json.dumps(context, indent=2)}""")

        # Send the user's question
        response = chat.send_message(question)
        return response.text

    @observe()
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """Summarize text.

        Args:
            text: Text to summarize
            max_sentences: Maximum sentences in summary

        Returns:
            Summary string
        """
        response = self.model.generate_content(
            contents=f"Summarize this in {max_sentences} sentences or less:\n\n{text}"
        )

        return response.text
    
    @observe()
    def _build_extraction_prompt(self, schema: dict) -> str:
        """Build prompt for structured extraction.

        Args:
            schema: JSON schema

        Returns:
            Formatted prompt
        """
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
    def extract_recipe(self, html: str) -> dict:
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
            generation_config=GenerationConfig(
                temperature=self.temperature,
                response_mime_type="application/json"
            )
        )

        if not response or not response.text:
            return None

        try:
            return json.loads(response.text)
        except:
            return None

    @observe()
    def generate_recipe_from_ingredients(self, ingredients, servings=1, dietary=None):
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
            generation_config=GenerationConfig(
                temperature=self.temperature,
                response_mime_type="application/json"
            )
        )

        if not response or not response.text:
            return None

        try:
            return json.loads(response.text)
        except:
            return None

    @observe()
    def ask_recipe_question(self, recipe: dict, question: str) -> str:
        """Ask Gemini a question about a recipe."""
        prompt = f"""
        You are a cooking assistant.

        Recipe:
        {json.dumps(recipe, indent=2)}

        Question:
        {question}
        """

        response = self.model.generate_content(
            contents=prompt,
            generation_config=GenerationConfig(
                temperature=self.temperature
            )
        )

        return response.text if response else None

    @observe()
    def validate_recipe(self, data: dict) -> dict:
        """Ensure recipe contains required fields."""
        return {
            "title": data.get("title"),
            "ingredients": data.get("ingredients", []),
            "instructions": data.get("instructions", []),
            "estimated_time_minutes": data.get("estimated_time") or data.get("estimated_time_minutes")
        }

