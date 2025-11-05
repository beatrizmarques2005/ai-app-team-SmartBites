# just a template

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


class AIService:
    """Service for all AI/LLM operations."""

    def __init__(self, model: str = "gemini-2.5-flash-lite"):
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
                temperature=0.1
            )
        )

        # ✅ Step 2: Check for empty or invalid response
        if not response.text or response.text.strip() == "":
            raise ValueError("Gemini returned an empty response. The file may be unclear or the schema too strict.")

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Gemini returned invalid JSON: {response.text}") from e


    @observe()
    def chat_with_context(
        self,
        question: str,
        context: dict,
        system_instruction: str = None
    ) -> str:
        """Chat with AI about specific context.

        Args:
            question: User's question
            context: Context data to reference
            system_instruction: Optional system instruction

        Returns:
            AI's answer as string
        """
        if system_instruction is None:
            system_instruction = "You are a helpful AI assistant analyzing data."

        chat = self.model.start_chat(
            model=self.model,
            config={
                'system_instruction': f"""{system_instruction}

Context data:
{json.dumps(context, indent=2)}"""
            }
        )

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
