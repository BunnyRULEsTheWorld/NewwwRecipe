"""Per-dimension rubric helpers, framed as neural-science-inspired cognitive-process mapping.

No brain-region claims. Each dimension maps to a cognitive process:
  - concept activation & analogy            (Ingredient Intelligence)
  - cross-ingredient flavor association     (Flavor Bridge Quality)
  - constrained divergent thinking          (Creative Leap)
  - exploratory search / fluency            (Exploration Value)
  - procedural planning / action feasibility(Culinary Feasibility)
  - linguistic encoding / narrative clarity  (Communication Quality)

The authoritative anchor texts live in each dimension's own SPEC (cie/dimensions/<key>.py).
This module provides shared rendering helpers used by the judge prompt.
"""
from __future__ import annotations

from typing import Any


def render_anchors(spec: Any) -> str:
    """Render a dimension spec's (score -> description) anchors as readable text."""
    return "\n".join(f"  {score}: {desc}" for score, desc in spec.anchors.items())


def cognitive_summary(spec: Any) -> str:
    """One-line cognitive-process summary for a dimension spec."""
    return f"{spec.label}: {spec.cognitive_mapping}"
