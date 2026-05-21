"""OpenAI LLM client wrapper with JSON parsing and retry logic."""
import asyncio
import json
import re
from typing import Any, Dict, Optional
from ..logging_config import get_logger
from ..config import settings
import openai

logger = get_logger("sentinelai.llm.client")

openai.api_key = settings.OPENAI_API_KEY or ""


class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini", max_retries: int = 3):
        self.model = model
        self.max_retries = max_retries

    async def call(self, prompt: str, *, temperature: float = 0.0) -> Any:
        """Call the LLM asynchronously and return parsed JSON output.

        Retries when the model returns non-JSON or invalid JSON.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug("LLM call attempt %d", attempt)
                resp = await asyncio.to_thread(
                    lambda: openai.ChatCompletion.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=1500,
                    )
                )
                text = resp.choices[0].message.content
                parsed = self._parse_json(text)
                return parsed
            except Exception as e:
                logger.warning("LLM parse attempt %d failed: %s", attempt, e)
                if attempt == self.max_retries:
                    logger.exception("LLM failed after retries")
                    raise
        raise RuntimeError("LLM call failed unexpectedly")

    def _parse_json(self, text: str) -> Any:
        # Try direct JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON substring
            m = re.search(r"\{.*\}\s*$|\[.*\]\s*$", text, re.S)
            if m:
                candidate = m.group(0)
                try:
                    return json.loads(candidate)
                except Exception:
                    pass
            # If all fails, raise
            raise ValueError("Failed to parse JSON from model output")
