import httpx
import pytest

from bot.llm.client import OllamaClient


@pytest.mark.asyncio
async def test_ollama_client_generate():
    async def handler(request):
        assert request.url.path == "/api/generate"
        return httpx.Response(200, json={"response": "Привет"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://ollama") as client:
        ollama = OllamaClient(
            base_url="http://ollama",
            model="qwen2.5:7b-instruct",
            timeout_seconds=10,
            temperature=0.2,
            max_output_tokens=50,
            client=client,
        )
        text = await ollama.generate("ping")
        assert text == "Привет"
