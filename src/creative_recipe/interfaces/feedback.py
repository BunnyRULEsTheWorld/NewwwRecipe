"""Feedback extension interface (not implemented in MVP).

Future: collect human ratings to calibrate CIE dimension weights (closed loop).
"""
from abc import ABC, abstractmethod
from typing import Optional


class FeedbackSink(ABC):
    """Abstract sink for user feedback on a realized recipe."""

    @abstractmethod
    def record(self, recipe_id: str, rating: float, comment: Optional[str] = None) -> None:
        """Persist a user rating for a recipe (e.g. thumbs / 1-5 score)."""
