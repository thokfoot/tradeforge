from __future__ import annotations


class GeminiProvider:
    def __init__(self, api_key: str, model: str = "gemini-flash-latest"):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    def generate(self, prompt: str) -> str:
        response = self._model.generate_content(prompt)
        return response.text
