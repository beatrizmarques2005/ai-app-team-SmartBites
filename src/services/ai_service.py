"""
AI Service - Handles all Gemini API interactions

This service is:
- Generic (doesn't know about contracts specifically)
- Reusable across different domains
- Fully traced with Langfuse
- Testable (can mock the client)
"""

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from langfuse import observe
import os
import json
import tempfile
import re
from dotenv import load_dotenv
import os

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

        # ✅ Step 2: Check for empty or invalid response
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

if __name__ == "__main__":
    print("Testing AIService...")
    ai_service = AIService()
    sample_schema = {
        "name": "string",
        "date_of_birth": "string",
        "address": "string"
    }
    # Assuming 'file_bytes' contains the bytes of a PDF or image file
    # extracted_data = ai_service.extract_structured(file_bytes, sample_schema)
    # print(extracted_data)