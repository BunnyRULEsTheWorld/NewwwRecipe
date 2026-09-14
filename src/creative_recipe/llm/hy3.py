"""Hy3 (Tencent Hunyuan via TokenHub) LLM provider — OpenAI-compatible.

Security / config contract:
  - The API key is read ONLY from the environment (via Config); it is NEVER hardcoded here.
  - The endpoint region comes from HY3_BASE_URL (env/config) and is NOT hardcoded to one region.
  - No secrets are logged.

Uses the OpenAI Python SDK in OpenAI-compatible mode. The SDK provides built-in retry and
timeout handling (configured via `timeout` / `max_retries`).
"""
import json
from typing import Any, Dict, List, Optional

import openai

from ..config import Config
from .base import LLMProvider


class Hy3LLMClient(LLMProvider):
    """OpenAI-compatible client for Hy3."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        *,
        # Hy3 (reasoning-class model) needs a generous timeout for the complex strict
        # structured schemas used by ideation / realization / CIE — a 60s ceiling aborts
        # real generations that legitimately take ~60-120s. This is connectivity config only;
        # it does not change model behaviour, prompts, or any output contract.
        timeout: float = 240.0,
        max_retries: int = 2,
    ) -> None:
        self.model = model
        # api_key / base_url are supplied by the caller (Config), never hardcoded.
        self._client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

    @classmethod
    def from_config(cls, cfg: Config) -> "Hy3LLMClient":
        """Build a client from a Config object (key/base_url/model all from env)."""
        return cls(api_key=cfg.hy3_api_key, base_url=cfg.hy3_base_url, model=cfg.hy3_model)

    @classmethod
    def from_env(cls, require_key: bool = True) -> "Hy3LLMClient":
        """Build a client by reading configuration from the environment."""
        return cls.from_config(Config.from_env(require_key=require_key))

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Plain chat completion. Extra kwargs (temperature, max_tokens, ...) pass through."""
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return resp.choices[0].message.content or ""

    def structured(self, messages: List[Dict[str, str]], schema: Optional[dict] = None, **kwargs: Any) -> dict:
        """JSON-mode completion, returned as a parsed dict.

        When `schema` is supplied it is passed straight through as `response_format`
        (expected shape: {"type": "json_schema", "json_schema": {...}} or {"type": "json_object"}).
        When omitted we fall back to plain JSON mode.
        """
        response_format: Any = {"type": "json_object"}
        if schema is not None:
            response_format = schema
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format=response_format,
            **kwargs,
        )
        content = resp.choices[0].message.content or "{}"
        return json.loads(content)
