import openai

class FlavorAI:
    def __init__(self, api_key: str):
        openai.api_key = api_key
    def suggestion(self, ingredients: list[str]) -> str:
        prompt = f"Suggest spices, herbs, juices, or condiments to enhance the flavor of these ingredients: {', '.join(ingredients)}"
        response = openai.ChatCompletion.create(
            model = "2.5-flashlite",
            messages=[{"role":"user", "content":prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()