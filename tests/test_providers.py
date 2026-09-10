"""Minimal provider-layer tests (P1).

Verifies that FakeProvider and Hy3LLMClient expose the SAME LLMProvider interface and
behave consistently, without requiring a real API key or network access.

The Hy3 client is exercised offline by mocking the OpenAI SDK at the module boundary.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from creative_recipe.config import Config
from creative_recipe.llm.base import LLMProvider
from creative_recipe.llm.fake import FakeProvider
from creative_recipe.llm.hy3 import Hy3LLMClient

MESSAGES = [{"role": "user", "content": "Hello"}]


def test_both_implement_llm_provider_interface():
    # Hy3LLMClient is a concrete subclass; FakeProvider is an instance of the interface.
    assert issubclass(Hy3LLMClient, LLMProvider)
    assert isinstance(FakeProvider(), LLMProvider)


def test_fake_provider_returns_str_and_dict():
    fake = FakeProvider()
    assert isinstance(fake.chat(MESSAGES), str)
    out = fake.structured(MESSAGES, schema={"type": "object"})
    assert isinstance(out, dict)
    assert out["ok"] is True


def test_hy3_provider_matches_interface_offline():
    cfg = Config(hy3_api_key="dummy", hy3_base_url="http://localhost/v1", hy3_model="hy3")

    # Patch the OpenAI SDK at the boundary so no network call is made.
    with patch("openai.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client

        # --- chat() ---
        chat_resp = MagicMock()
        chat_resp.choices = [MagicMock(message=MagicMock(content="hello"))]
        mock_client.chat.completions.create.return_value = chat_resp

        client = Hy3LLMClient.from_config(cfg)
        assert isinstance(client, LLMProvider)
        assert client.chat(MESSAGES) == "hello"

        # --- structured() returns a parsed dict ---
        struct_resp = MagicMock()
        struct_resp.choices = [MagicMock(message=MagicMock(content=json.dumps({"score": 8})))]
        mock_client.chat.completions.create.return_value = struct_resp

        parsed = client.structured(MESSAGES, schema={"type": "object"})
        assert parsed == {"score": 8}


def test_config_requires_api_key(monkeypatch):
    # Keep this test isolated from a developer's real, git-ignored .env file.
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.delenv("HY3_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        Config.from_env(require_key=True)


def test_config_reads_env(monkeypatch):
    monkeypatch.setenv("HY3_API_KEY", "sk-test")
    monkeypatch.setenv("HY3_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("HY3_MODEL", "hy3-custom")
    cfg = Config.from_env()
    assert cfg.hy3_api_key == "sk-test"
    assert cfg.hy3_base_url == "https://example.com/v1"
    assert cfg.hy3_model == "hy3-custom"
    assert cfg.num_concepts == 5  # defaults preserved
