"""Lightweight LLM client with provider selection (Groq / OpenAI).

This module implements a minimal Groq-backed client using `requests` and
keeps OpenAI usage optional and lazy. When `LLM_PROVIDER` is set to "groq",
the client will POST to the Groq inference endpoint using `GROQ_API_KEY` and
`MODEL_NAME` environment variables. If `LLM_PROVIDER` is "openai", the OpenAI
SDK will be imported lazily.

If no provider is configured the client will raise at call-time so callers can
fall back to demo behavior.
"""
import asyncio
import json
import os
import re
from typing import Any
from ..logging_config import get_logger
from ..config import settings

logger = get_logger("sentinelai.llm.client")


class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini", max_retries: int = 3):
        self.model = model
        self.max_retries = max_retries

    async def call(self, prompt: str, *, temperature: float = 0.0) -> Any:
        """Call the configured LLM provider and return parsed JSON output.

        Supports `LLM_PROVIDER=groq` and `LLM_PROVIDER=openai` (optional).
        """
        provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
        if provider == "groq":
            return await self._call_groq(prompt)
        if provider == "openai":
            return await self._call_openai(prompt, temperature=temperature)

        raise RuntimeError("No LLM provider configured (set LLM_PROVIDER). Running in demo/offline mode.")

    async def _call_openai(self, prompt: str, *, temperature: float = 0.0) -> Any:
        # Lazy import of openai to keep runtime lightweight when not used
        try:
            import openai
        except Exception as e:
            logger.error("OpenAI SDK not installed: %s", e)
            raise

        openai.api_key = os.environ.get("OPENAI_API_KEY", "") or settings.OPENAI_API_KEY or ""

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug("OpenAI call attempt %d", attempt)
                resp = await asyncio.to_thread(
                    lambda: openai.ChatCompletion.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=1500,
                    )
                )
                text = resp.choices[0].message.content
                return self._parse_json(text)
            except Exception as e:
                logger.warning("OpenAI attempt %d failed: %s", attempt, e)
                if attempt == self.max_retries:
                    logger.exception("OpenAI failed after retries")
                    raise

    async def _call_groq(self, prompt: str) -> Any:
        """Minimal Groq client using `requests`.

        The endpoint URL is constructed as:
          https://api.groq.com/v1/models/{MODEL_NAME}/generate

        The response parsing is tolerant to several JSON shapes.
        """
        import requests

        key = os.environ.get("GROQ_API_KEY")
        model = os.environ.get("MODEL_NAME") or self.model
        if not key:
            raise RuntimeError("GROQ_API_KEY is not set for Groq provider")

        url = f"https://api.groq.com/v1/models/{model}/generate"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {"input": prompt}

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug("Groq call attempt %d -> %s", attempt, url)
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                # tolerant extraction of text
                text = None
                if isinstance(data, dict):
                    # common keys
                    text = data.get("output") or data.get("text") or data.get("generated_text")
                    if not text and "choices" in data and data["choices"]:
                        ch = data["choices"][0]
                        text = ch.get("text") or ch.get("message", {}).get("content")
                if text is None:
                    # fallback: stringify JSON
                    text = json.dumps(data)

                return self._parse_json(text)
            except Exception as e:
                logger.warning("Groq attempt %d failed: %s", attempt, e)
                if attempt == self.max_retries:
                    logger.exception("Groq failed after retries")
                    raise

    def _parse_json(self, text: str) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}\s*$|\[.*\]\s*$", text, re.S)
            if m:
                candidate = m.group(0)
                try:
                    return json.loads(candidate)
                except Exception:
                    pass
            raise ValueError("Failed to parse JSON from model output")
