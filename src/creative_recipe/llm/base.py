"""Abstract LLM provider interface (adapter boundary).

The rest of the system depends ONLY on this interface, so the concrete backend (Hy3, or a
mock for tests) can be swapped without touching business logic.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMProvider(ABC):
    """Unified LLM interface. Hy3 is the default concrete implementation."""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Return assistant text for a chat message list."""

    @abstractmethod
    def structured(self, messages: List[Dict[str, str]], schema: Optional[dict] = None, **kwargs: Any) -> dict:
        """Return a parsed JSON object (dict) for a chat message list.

        `schema` is reserved for strict JSON-schema validation in later phases (P2/P4);
        the default implementation requests JSON mode and parses the response.
        """
