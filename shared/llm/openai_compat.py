"""
OpenAI-Compatible LLM Client
=============================
Async HTTP client for OpenAI-compatible APIs (vLLM, Ollama, OpenAI).

Supports:
- vLLM OpenAI API server
- Ollama with OpenAI compatibility
- OpenAI API
- Any OpenAI-compatible endpoint

Usage:
    from shared.llm.openai_compat import CLIENT

    response = await CLIENT.chat(
        model='Qwen2.5-7B-Instruct',
        system='You are a helpful assistant',
        user='Hello!',
        max_tokens=200,
        timeout=8.0
    )
"""

from __future__ import annotations
from typing import Optional
import httpx
from shared.config.llm import CFG


class LLMClient:
    """
    Async HTTP client for OpenAI-compatible LLM APIs.

    Attributes:
        base_url: API endpoint base URL
        api_key: API key for authentication
        headers: HTTP headers with authorization
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize LLM client.

        Args:
            base_url: Override default base URL from config
            api_key: Override default API key from config
        """
        self.base_url = base_url or CFG.base_url
        self.api_key = api_key or CFG.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Send chat completion request.

        Args:
            model: Model name (e.g., 'Qwen2.5-7B-Instruct')
            system: System prompt
            user: User message
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generated text response

        Raises:
            httpx.HTTPError: On API error
            httpx.TimeoutException: On timeout

        Example:
            >>> response = await CLIENT.chat(
            ...     model='Qwen2.5-7B-Instruct',
            ...     system='You are a helpful assistant',
            ...     user='What is 2+2?'
            ... )
            >>> print(response)
            '2+2 equals 4.'
        """
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens or CFG.max_tokens,
        }

        t = timeout or CFG.request_timeout

        async with httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers, timeout=t
        ) as cli:
            r = await cli.post("/chat/completions", json=data)
            r.raise_for_status()
            js = r.json()
            return js["choices"][0]["message"]["content"].strip()


# Global client instances
CLIENT = LLMClient()  # Backward compatibility (uses local)
CLIENT_LOCAL = LLMClient(base_url=CFG.base_url_local, api_key=CFG.api_key_local)
CLIENT_DEEPSEEK = LLMClient(
    base_url=CFG.base_url_deepseek, api_key=CFG.api_key_deepseek
)
