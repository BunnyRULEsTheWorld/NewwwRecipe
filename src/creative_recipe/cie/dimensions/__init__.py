"""Six CIE dimension implementations (one file per dimension) + the registry/hub.

This package IS the tunable hub of the Creative Innovation Evaluation Framework:
  - `WEIGHTS`  : default six-dimension weights (sum = 1.0)
  - `STAGE_A_KEYS` / `STAGE_B_KEYS` : which dimensions run at which stage
  - `REGISTRY` : key -> DimensionSpec (each spec is self-contained in its own file)
  - `STAGE_A_SPECS` / `STAGE_B_SPECS` : ordered spec lists for the two stages

To add a dimension: create `cie/dimensions/<key>.py` exporting a `SPEC` and register it here.

CANONICAL CONTRACT (CIE v3)
---------------------------
The six dimensions and their weights mirror `CIE-Culinary-Bench/schema/scoring_rubric.json`:

    culinary_knowledge_grounding        0.15  (Stage A)
    existing_culinary_precedent_analysis 0.15  (Stage A)
    innovation_delta_quality            0.25  (Stage A)
    mechanistic_plausibility            0.20  (Stage A)
    innovation_value                    0.15  (Stage A)
    realization_quality                 0.10  (Stage B)

The final total is the direct six-dimension weighted sum (see cie.scorer.total_score).
There is NO stage-level blend such as the historical 0.75 / 0.25.

Historical migration note (deprecated, for readers of older commits only): the previous set was
`ingredient_intelligence` / `flavor_bridge_quality` / `creative_leap` / `exploration_value` /
`culinary_feasibility` / `communication_quality`. Those keys are no longer registered here and
must not appear in any contract. See `docs/cie_framework.md`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from ...types import Stage


@dataclass
class DimensionSpec:
    """Self-contained definition of one CIE dimension."""

    key: str
    label: str
    stage: Stage
    weight: float
    cognitive_mapping: str
    anchors: Dict[int, str]  # score (1-5) -> description
    build_messages: Callable[[Any, Optional[dict]], List[dict]]
    question: str = ""  # canonical one-line question (from scoring_rubric.json)


# --- Default weights (sum = 1.0), per CIE v3 -----------------------------------------------
WEIGHTS: Dict[str, float] = {
    "culinary_knowledge_grounding": 0.15,
    "existing_culinary_precedent_analysis": 0.15,
    "innovation_delta_quality": 0.25,
    "mechanistic_plausibility": 0.20,
    "innovation_value": 0.15,
    "realization_quality": 0.10,
}

# Stage A evaluates the five concept-level dimensions (candidate ranking / Top-K).
STAGE_A_KEYS: tuple[str, ...] = (
    "culinary_knowledge_grounding",
    "existing_culinary_precedent_analysis",
    "innovation_delta_quality",
    "mechanistic_plausibility",
    "innovation_value",
)
# Stage B evaluates only realization_quality, which needs the realized Recipe.
STAGE_B_KEYS: tuple[str, ...] = ("realization_quality",)

# --- Register each dimension (importing the self-contained spec files) -----------------
from .culinary_knowledge_grounding import SPEC as _culinary_knowledge_grounding  # noqa: E402
from .existing_culinary_precedent_analysis import SPEC as _existing_culinary_precedent_analysis  # noqa: E402
from .innovation_delta_quality import SPEC as _innovation_delta_quality  # noqa: E402
from .mechanistic_plausibility import SPEC as _mechanistic_plausibility  # noqa: E402
from .innovation_value import SPEC as _innovation_value  # noqa: E402
from .realization_quality import SPEC as _realization_quality  # noqa: E402

REGISTRY: Dict[str, DimensionSpec] = {
    _culinary_knowledge_grounding.key: _culinary_knowledge_grounding,
    _existing_culinary_precedent_analysis.key: _existing_culinary_precedent_analysis,
    _innovation_delta_quality.key: _innovation_delta_quality,
    _mechanistic_plausibility.key: _mechanistic_plausibility,
    _innovation_value.key: _innovation_value,
    _realization_quality.key: _realization_quality,
}

STAGE_A_SPECS: List[DimensionSpec] = [REGISTRY[k] for k in STAGE_A_KEYS]
STAGE_B_SPECS: List[DimensionSpec] = [REGISTRY[k] for k in STAGE_B_KEYS]


def get_spec(key: str) -> DimensionSpec:
    return REGISTRY[key]
