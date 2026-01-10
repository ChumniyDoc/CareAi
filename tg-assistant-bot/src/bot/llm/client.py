from __future__ import annotations

import datetime as dt

import httpx

from bot.llm.state import LLM_STATUS


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: int,
        temperature: float,
        max_output_tokens: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._client = client

    async def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_output_tokens,
            },
        }
        client = self._client or httpx.AsyncClient(timeout=self.timeout_seconds)
        try:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            text = data.get("response", "").strip()
            if text:
                LLM_STATUS.last_success_at = dt.datetime.now(dt.timezone.utc)
                LLM_STATUS.last_error = None
            return text
        except httpx.HTTPError as exc:
            LLM_STATUS.last_error = str(exc)
            raise
        finally:
            if self._client is None:
                await client.aclose()
