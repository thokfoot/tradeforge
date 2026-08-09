from __future__ import annotations


class GroqProvider:
    """Layer 3 brain — Groq API free tier (llama-3-70b-8192)."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3-70b-8192",
        base_url: str = "https://api.groq.com/openai/v1/chat/completions",
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url

    def generate(self, prompt: str) -> str:
        import httpx

        resp = httpx.post(
            self._base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 500,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        body = resp.json()
        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError):
            raise RuntimeError("unexpected Groq response")


class GeminiProvider:
    """Gemini Flash fallback (reuses google-generativeai already in requirements)."""

    def __init__(self, api_key: str, model: str = "gemini-flash-latest"):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    def generate(self, prompt: str) -> str:
        return self._model.generate_content(prompt).text


class CloudflareParser:
    """Layer 1 listener — Cloudflare Workers AI (free, serverless)."""

    def __init__(self, url: str, token: str):
        self._url = url
        self._token = token

    def parse(self, text: str) -> dict:
        import httpx

        resp = httpx.post(
            self._url,
            headers={"Authorization": f"Bearer {self._token}"},
            json={"text": text},
            timeout=20.0,
        )
        resp.raise_for_status()
        body = resp.json()
        dsl = (body.get("dsl") if isinstance(body, dict) else None) or {}
        if not isinstance(dsl, dict):
            raise RuntimeError("unexpected Cloudflare parser response")
        return dsl
