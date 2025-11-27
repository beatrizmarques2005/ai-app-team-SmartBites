import json
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from langfuse import observe

class FlavorAI:
    """AI service suggesting flavor enhancements for ingredients using Gemini."""

    def __init__(self, api_key: str, model_name="gemini-1.5-flash", temperature=0.7):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=model_name)
        self.temperature = temperature

    @observe()
    def suggestion(self, ingredients: list[str]) -> list[str]:
        prompt = f"""
        You are a culinary AI assistant.
        Suggest spices, herbs, juices, or condiments to enhance the flavor of these ingredients: {', '.join(ingredients)}.
        Return the result as a JSON array of strings.
        """
        response = self.model.generate_content(
            contents=prompt,
            generation_config=GenerationConfig(temperature=self.temperature)
        )
        try:
            return json.loads(response.text)
        except:
            # fallback: return as comma-separated list
            return [r.strip() for r in response.text.split(",") if r.strip()]
