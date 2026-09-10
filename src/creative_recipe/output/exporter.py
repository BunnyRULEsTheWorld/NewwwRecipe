"""Export a PipelineResult to JSON."""
from __future__ import annotations

import json
from typing import Optional

from ..types import PipelineResult


def export(result: PipelineResult, path: str) -> str:
    """Write the result as pretty JSON; returns the path written."""
    data = result.model_dump(mode="json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def to_json(result: PipelineResult) -> str:
    """Serialize a result to a JSON string (for APIs / logging)."""
    return result.model_dump_json(indent=2)
