"""
LLM Configuration
=================
OpenAI-compatible LLM endpoint configuration for local RTX 5090 or cloud APIs.

Supports:
- vLLM (local GPU server)
- Ollama (local models)
- OpenAI API (cloud)
- Any OpenAI-compatible endpoint

Environment Variables:
    LLM_BASE_URL: API endpoint (default: http://127.0.0.1:8001/v1)
    LLM_API_KEY: API key (default: sk-local-placeholder)
    LLM_MODEL_KO: Korean model (default: Qwen2.5-7B-Instruct)
    LLM_MODEL_ZH: Chinese model (default: Qwen2.5-7B-Instruct)
    LLM_MODEL_EN: English model (default: Llama-3.1-8B-Instruct)
    LLM_TIMEOUT: Request timeout in seconds (default: 8.0)
    LLM_MAX_TOKENS: Max tokens per response (default: 200)

Example .env:
    LLM_BASE_URL=http://127.0.0.1:8001/v1
    LLM_API_KEY=sk-local
    LLM_MODEL_KO=Qwen2.5-7B-Instruct
    LLM_MODEL_ZH=Qwen2.5-7B-Instruct
    LLM_MODEL_EN=Llama-3.1-8B-Instruct
    LLM_TIMEOUT=8.0
    LLM_MAX_TOKENS=220
"""

from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """
    LLM configuration with hybrid routing (local + cloud).

    Supports:
    - Local server (vLLM/Ollama) for Korean/English
    - Cloud API (DeepSeek) for Chinese

    Attributes:
        base_url_local: Local LLM server endpoint (RTX 5090)
        api_key_local: Local API key
        base_url_deepseek: DeepSeek cloud API endpoint
        api_key_deepseek: DeepSeek API key
        model_ko: Model for Korean (local)
        model_en: Model for English (local)
        model_zh: Model for Chinese (cloud)
        request_timeout: Request timeout in seconds
        max_tokens: Maximum tokens per response
    """

    # Local server (vLLM / Ollama) - RTX 5090
    base_url_local: str = os.getenv("LLM_BASE_URL_LOCAL", "http://127.0.0.1:8001/v1")
    api_key_local: str = os.getenv("LLM_API_KEY_LOCAL", "sk-local")

    # Cloud server (DeepSeek)
    base_url_deepseek: str = os.getenv(
        "LLM_BASE_URL_DEEPSEEK", "https://api.deepseek.com/v1"
    )
    api_key_deepseek: str = os.getenv("LLM_API_KEY_DEEPSEEK", "")

    # Language-specific models
    model_ko: str = os.getenv("LLM_MODEL_KO", "Qwen2.5-7B-Instruct")  # Local
    model_en: str = os.getenv("LLM_MODEL_EN", "Llama-3.1-8B-Instruct")  # Local
    model_zh: str = os.getenv("LLM_MODEL_ZH", "deepseek-chat")  # Cloud

    # Request parameters
    request_timeout: float = float(os.getenv("LLM_TIMEOUT", "8.0"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "200"))

    # Backward compatibility (deprecated)
    @property
    def base_url(self) -> str:
        """Deprecated: Use base_url_local instead"""
        return self.base_url_local

    @property
    def api_key(self) -> str:
        """Deprecated: Use api_key_local instead"""
        return self.api_key_local


# Global configuration instance
CFG = LLMConfig()
