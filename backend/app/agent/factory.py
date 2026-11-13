"""Provider-Agnostic LLM Factory for Autonomous ML Research Agent.

Seamlessly instantiates and manages free-tier and sustainable models:
- Google Gemini 2.5 Flash / 1.5 Flash (Default Cloud - Free via AI Studio)
- Groq Cloud Llama 3.3 70B (High Speed Cloud - Free Developer Tier)
- Local Ollama Qwen 2.5 / Llama 3.1 (100% Offline & Private)
- Deterministic Mock Provider (Zero API Key Unit Testing & CI/CD)
"""

import os
import json
import httpx
from typing import Dict, Any, List, Optional, Tuple
from ..config import settings


class BaseLLMAdapter:
    """Base interface for model providers."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools_manifest: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini Flash adapter using google.generativeai / REST API."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        super().__init__(model_name)
        self.api_key = api_key

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools_manifest: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        # Formulate prompt from multi-turn messages
        last_user_msg = messages[-1]["content"] if messages else ""

        # Direct Google AI REST endpoint with resilient model fallbacks
        models_to_try = [self.model_name]
        for fallback in ["gemini-3.8-flash", "gemini-3.5-flash-lite"]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        payload = {
            "contents": [{"parts": [{"text": last_user_msg}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
        }

        last_error = None
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            for model in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        text = ""
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            text = "".join(p.get("text", "") for p in parts)

                        usage = data.get("usageMetadata", {})
                        prompt_tokens = usage.get("promptTokenCount", len(last_user_msg) // 4)
                        completion_tokens = usage.get("candidatesTokenCount", len(text) // 4)

                        return {
                            "text": text,
                            "provider": "gemini",
                            "model": model,
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "cost_usd": 0.00,  # Free tier
                        }
                    else:
                        last_error = f"Gemini API ({model}) returned {resp.status_code}: {resp.text[:200]}"
                except Exception as exc:
                    last_error = f"Connection error for {model}: {str(exc)}"

        raise RuntimeError(last_error or "All Gemini model endpoints failed.")


class GroqAdapter(BaseLLMAdapter):
    """Groq Cloud adapter utilizing OpenAI-compatible high-speed API with model fallback."""

    def __init__(self, api_key: str, model_name: str = "openai/gpt-oss-120b"):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools_manifest: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        models_to_try = [self.model_name]
        for fallback in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "llama-3.3-70b-versatile"]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        last_error = None
        async with httpx.AsyncClient(timeout=20.0) as client:
            for model in models_to_try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.2,
                }
                try:
                    resp = await client.post(self.base_url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choice = data["choices"][0]
                        text = choice["message"]["content"]
                        usage = data.get("usage", {})

                        return {
                            "text": text,
                            "provider": "groq",
                            "model": model,
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "cost_usd": 0.00,  # Free tier
                        }
                    else:
                        last_error = f"Groq API error for model {model} ({resp.status_code}): {resp.text[:200]}"
                except Exception as exc:
                    last_error = f"Connection error for Groq model {model}: {str(exc)}"

        raise RuntimeError(last_error or "All Groq model endpoints failed.")


class OllamaAdapter(BaseLLMAdapter):
    """Local Ollama adapter for 100% offline, air-gapped execution."""

    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "qwen2.5:14b"):
        super().__init__(model_name)
        self.base_url = f"{base_url.rstrip('/')}/api/chat"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools_manifest: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.base_url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Ollama server error {resp.status_code}: {resp.text[:200]}")
            data = resp.json()

            text = data.get("message", {}).get("content", "")
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            return {
                "text": text,
                "provider": "ollama",
                "model": self.model_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost_usd": 0.00,  # Self-hosted 0.00
            }


class MockLLMAdapter(BaseLLMAdapter):
    """Deterministic Mock Adapter for unit testing, CI/CD, and offline verification."""

    def __init__(self, model_name: str = "mock-reasoning-v1"):
        super().__init__(model_name)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools_manifest: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        query = messages[-1]["content"].lower() if messages else ""
        if "paper" in query or "arxiv" in query or "research" in query:
            text = "I recommend investigating state-of-the-art literature on this topic. Let me search arXiv for the top verified preprints."
        elif "dataset" in query or "kaggle" in query:
            text = "I have identified matching high-usability Kaggle datasets for benchmark evaluation."
        elif "clean" in query or "pipeline" in query:
            text = "The data cleaning pipeline is ready to normalize headers, impute null values, and remove duplicates. Please confirm execution."
        else:
            text = f"Analyzing your research query: '{messages[-1]['content'] if messages else ''}'. Sourcing literature and datasets now."

        return {
            "text": text,
            "provider": "mock",
            "model": self.model_name,
            "prompt_tokens": len(query) // 4,
            "completion_tokens": len(text) // 4,
            "cost_usd": 0.00,
        }


def get_model_adapter(provider_override: Optional[str] = None) -> BaseLLMAdapter:
    """Factory function returning the configured LLM adapter."""
    provider = (provider_override or settings.MODEL_PROVIDER).lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            # Graceful fallback to mock if API key is not yet set
            return MockLLMAdapter(model_name="mock-gemini-fallback")
        return GeminiAdapter(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)

    elif provider == "groq":
        if not settings.GROQ_API_KEY:
            return MockLLMAdapter(model_name="mock-groq-fallback")
        return GroqAdapter(api_key=settings.GROQ_API_KEY, model_name=settings.GROQ_MODEL)

    elif provider == "ollama":
        return OllamaAdapter(base_url=settings.OLLAMA_BASE_URL, model_name=settings.OLLAMA_MODEL)

    elif provider == "mock":
        return MockLLMAdapter()

    else:
        # Default fallback
        return MockLLMAdapter(model_name=f"mock-{provider}")
