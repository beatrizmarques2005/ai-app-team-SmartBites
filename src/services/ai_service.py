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
    def extract_recipe_from_html(self, html: str) -> dict:
        """Extract structured recipe data from raw HTML using Gemini."""

        prompt = f"""
        Extract a recipe from the following HTML.
        Return ONLY valid JSON.

        The JSON structure must be:

        {{
          "title": "string",
          "ingredients": ["string", ...],
          "instructions": ["string", ...],
          "estimated_time_minutes": int
        }}

        HTML:
        {html}
        """

        response = self.model.generate_content(
            contents=prompt,
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                temperature=temperature,
            ),
        )

        raw = response.text.strip()

        if raw.startswith("```json") or raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.DOTALL).strip()

        return json.loads(raw)

    @observe()
    def ask_recipe_question(self, recipe: dict, question: str) -> str:
        """Ask Gemini about a recipe in JSON format."""
        
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
                temperature=temperature,
            )
        )

        return response.text

    @observe()
    def validate_recipe(self, data: dict) -> dict:
        """Ensure recipe contains required fields."""
        return {
            "title": data.get("title", None),
            "ingredients": data.get("ingredients", []),
            "instructions": data.get("instructions", []),
            "estimated_time_minutes": data.get("estimated_time_minutes", None),
        }




if __name__ == "__main__":
    print("Testing AIService...")
    ai_service = AIService()

    sample_schema = {
        "name": "string",
        "date_of_birth": "string",
        "address": "string"
    }

    # Try to run structured extraction if a sample file is available (path from env or default sample.pdf)
    sample_path = os.getenv("SAMPLE_FILE", "sample.pdf")
    p = pathlib.Path(sample_path)
    if p.exists():
        try:
            file_bytes = p.read_bytes()
            extracted_data = ai_service.extract_structured(file_bytes, sample_schema, mime_type="application/pdf")
            print("Extracted structured data:")
            print(json.dumps(extracted_data, indent=2))
        except Exception as e:
            print("Extraction error:", e)
    else:
        print(f"No sample file found at {sample_path}, skipping extract_structured test.")

    # Quick summarize test
    try:
        sample_text = (
            "SmartBites is a meal-recommendation application that analyzes recipes, menus, "
            "and food labels to provide personalized dietary insights. It helps users make "
            "healthier choices by flagging allergens and intolerances, suggesting substitutions, "
            "and tailoring recommendations to dietary goals and preferences."
        )
        print("\nSummary:")
        print(ai_service.summarize(sample_text, max_sentences=2))
    except Exception as e:
        print("Summarize error:", e)

    # Quick chat_with_context test
    try:
        context = {"app": "SmartBites", "feature": "nutrition analysis"}
        print("\nChat response:")
        print(ai_service.chat_with_context("How can this feature help users?", context))
    except Exception as e:
        print("Chat error:", e)

