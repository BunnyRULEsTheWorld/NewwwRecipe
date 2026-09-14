"""Pydantic request/response models for the thin web API adapter.

Scope: these models are a *transport* layer only. They mirror the existing canonical CIE v3
domain contract (`creative_recipe.types`) and never redefine recipe generation or scoring rules:

* the Innovation Trace is the canonical SIX-stage object, keyed exactly as in
  `CIE-Culinary-Bench/schema/cie_sample.schema.json`;
* the CIE scores are the canonical SIX dimensions with the canonical weights
  (0.15 / 0.15 / 0.25 / 0.20 / 0.15 / 0.10), each an integer 1-5;
* the total is the backend's direct six-dimension weighted sum (`cie.scorer.total_score`).
  It is NEVER recomputed here with a historic Stage-A/Stage-B blend.

No secret (API key, base URL, token) is ever part of a response model.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..cie.dimensions import WEIGHTS
from ..types import CIEStageDimensions


# --- Canonical CIE v3 vocabulary (single source: the existing backend) --------------------
CANONICAL_DIMENSION_KEYS: tuple[str, ...] = tuple(CIEStageDimensions.ALL)

#: Human-facing labels for the six canonical dimensions (keys stay canonical).
DIMENSION_LABELS: dict[str, str] = {
    "culinary_knowledge_grounding": "Culinary Knowledge Grounding",
    "existing_culinary_precedent_analysis": "Existing Culinary Precedent Analysis",
    "innovation_delta_quality": "Innovation Delta Quality",
    "mechanistic_plausibility": "Mechanistic Plausibility",
    "innovation_value": "Innovation Value",
    "realization_quality": "Realization Quality",
}

#: One-line plain-language explanation shown in the UI next to each dimension.
DIMENSION_EXPLANATIONS: dict[str, str] = {
    "culinary_knowledge_grounding": (
        "Does the idea use real ingredient and technique knowledge, with honest limits?"
    ),
    "existing_culinary_precedent_analysis": (
        "Has it correctly identified the closest existing dishes, and how this departs from them?"
    ),
    "innovation_delta_quality": (
        "Is the actual change meaningful and well specified — not just 'unusual for the sake of it'?"
    ),
    "mechanistic_plausibility": (
        "Is there a real flavour, texture or cooking mechanism explaining why it should work?"
    ),
    "innovation_value": (
        "Is the exploration worth trying, even after discounting mere novelty?"
    ),
    "realization_quality": (
        "Plan-level check: is the written recipe complete, consistent and actually cookable? "
        "Capped at 4 — level 5 is reserved for a future empirical pipeline."
    ),
}

#: Canonical six-stage Innovation Trace order and human titles.
TRACE_STAGE_KEYS: tuple[str, ...] = (
    "existing_culinary_context",
    "ingredient_and_technique_knowledge",
    "innovation_delta",
    "mechanistic_justification",
    "creative_hypothesis",
    "risk_and_constraint",
)

TRACE_STAGE_LABELS: dict[str, str] = {
    "existing_culinary_context": "Existing Culinary Context",
    "ingredient_and_technique_knowledge": "Ingredient & Technique Knowledge",
    "innovation_delta": "Innovation Delta",
    "mechanistic_justification": "Mechanistic Justification",
    "creative_hypothesis": "Creative Hypothesis",
    "risk_and_constraint": "Risk & Constraint",
}

TRACE_STAGE_SUMMARIES: dict[str, str] = {
    "existing_culinary_context": "What already exists that this idea departs from.",
    "ingredient_and_technique_knowledge": "The ingredient and technique knowledge it leans on.",
    "innovation_delta": "The concrete before → after change.",
    "mechanistic_justification": "Why the change should work, in cooking terms.",
    "creative_hypothesis": "The novel idea being proposed.",
    "risk_and_constraint": "What could fail, what is traded away, and how to judge failure.",
}


# --- Preferences ---------------------------------------------------------------------------
CUISINE_DIRECTIONS = ("surprise-me", "chinese", "western", "fusion")
FLAVOR_PREFERENCES = ("balanced", "savory", "spicy", "fresh", "rich")
TIME_PREFERENCES = ("any", "under-20", "under-40", "weekend")

CuisineDirection = Literal["surprise-me", "chinese", "western", "fusion"]
FlavorPreference = Literal["balanced", "savory", "spicy", "fresh", "rich"]
TimePreference = Literal["any", "under-20", "under-40", "weekend"]


class Preferences(BaseModel):
    """Optional, user-facing generation preferences (never silently dropped)."""

    model_config = ConfigDict(extra="forbid")

    cuisine: CuisineDirection = Field(
        "fusion", description="Cuisine direction; defaults to East-West Fusion."
    )
    flavor: FlavorPreference = Field("balanced", description="Target flavour profile.")
    time: TimePreference = Field("any", description="Time budget.")
    constraints: Optional[str] = Field(
        None,
        max_length=400,
        description="Free-text constraints: allergies, dietary needs, mood...",
    )

    # --- Human-readable rendering (fed into the existing `constraints` pipeline input) ----
    _CUISINE_TEXT = {
        "surprise-me": "Surprise me (no fixed cuisine direction)",
        "chinese": "Chinese-inspired",
        "western": "Western-inspired",
        "fusion": "East-West Fusion",
    }
    _FLAVOR_TEXT = {
        "balanced": "Balanced",
        "savory": "Savory",
        "spicy": "Spicy",
        "fresh": "Fresh",
        "rich": "Rich",
    }
    _TIME_TEXT = {
        "any": "Any duration",
        "under-20": "Under 20 minutes",
        "under-40": "Under 40 minutes",
        "weekend": "Weekend project (time is not a constraint)",
    }

    def to_display_lines(self) -> List[str]:
        return [
            f"Cuisine direction: {self._CUISINE_TEXT[self.cuisine]}",
            f"Flavor profile: {self._FLAVOR_TEXT[self.flavor]}",
            f"Time budget: {self._TIME_TEXT[self.time]}",
        ]


class GenerateRequest(BaseModel):
    """POST /api/recipes/generate request body."""

    model_config = ConfigDict(extra="forbid")

    ingredients: List[str] = Field(
        ...,
        min_length=2,
        max_length=20,
        description="Selected ingredient ids (canonical snake_case stems), at least two.",
    )
    preferences: Preferences = Field(default_factory=Preferences)
    avoid: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Recipe titles already shown; the pipeline is asked not to repeat them.",
    )
    demo: Optional[bool] = Field(
        None,
        description="Force demo mode on/off. Defaults to automatic (demo when no API key is configured).",
    )


# --- Responses ------------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    demo_mode: bool
    provider: str
    model: str
    ingredient_count: int
    scene_asset_count: int
    missing_ingredient_files: List[str]
    missing_scene_files: List[str]


class IngredientItem(BaseModel):
    id: str
    displayName: str
    filename: str
    category: str
    aliases: List[str] = Field(default_factory=list)
    url: str


class CategoryItem(BaseModel):
    id: str
    label: str


class IntegrityItem(BaseModel):
    expectedCount: int
    missingFiles: List[str]
    orphanFiles: List[str]
    missingSceneFiles: List[str]


class IngredientsResponse(BaseModel):
    count: int
    categories: List[CategoryItem]
    ingredients: List[IngredientItem]
    integrity: IntegrityItem


class RecipeIngredient(BaseModel):
    name: str
    quantity: Optional[str] = None
    note: Optional[str] = None


class RecipePayload(BaseModel):
    name: str
    ingredients: List[RecipeIngredient] = Field(default_factory=list)
    seasonings: List[RecipeIngredient] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    creative_explanation: str = ""
    creative_hypothesis: Optional[str] = None
    concept_name: Optional[str] = None
    servings: Optional[str] = None
    estimated_time: Optional[str] = None
    difficulty: Optional[str] = None


class ConceptPayload(BaseModel):
    name: str
    ingredients: List[str] = Field(default_factory=list)
    creative_angle: str = ""
    core_idea: str = ""


class DimensionScore(BaseModel):
    key: str
    label: str
    weight: float
    score: int = Field(..., ge=1, le=5)
    reason: str
    stage: str
    explanation: str


class CiePayload(BaseModel):
    total_score: float = Field(..., description="Canonical direct six-dimension weighted sum (1-5).")
    scale_min: int = 1
    scale_max: int = 5
    dimensions: List[DimensionScore]
    stage_a_score: float = Field(0.0, description="Secondary diagnostic aggregate (Stage A).")
    stage_b_score: float = Field(0.0, description="Secondary diagnostic aggregate (Stage B).")
    weights: dict[str, float] = Field(default_factory=lambda: dict(WEIGHTS))


class TraceStage(BaseModel):
    key: str
    index: int
    label: str
    summary: str
    content: dict


class TracePayload(BaseModel):
    stages: List[TraceStage]
    creative_hypothesis: Optional[str] = None
    risk_notes: Optional[str] = None


class GenerationMeta(BaseModel):
    provider: str
    demo_mode: bool
    model: str
    requested_ingredients: List[str]
    requested_preferences: Preferences
    concept_count: int
    recipe_count: int
    rank: Optional[int] = None
    #: Set only when a requested live (Hy3) generation failed and we gracefully
    #: fell back to the offline DemoProvider. Absent/None means no fallback.
    fallback_reason: Optional[str] = None


class GenerateResponse(BaseModel):
    recipe: RecipePayload
    concept: Optional[ConceptPayload] = None
    trace: Optional[TracePayload] = None
    cie: Optional[CiePayload] = None
    meta: GenerationMeta
