"""Core data structures for Creative Recipe AI (base types, P0).

These types are the contract between pipeline stages:

    Ingredient
      -> Ingredient Understanding
      -> Creative Ideation  (produces the six-stage InnovationTrace + RecipeConcept)
      -> Stage-A CIE        (5 concept-level dimensions: Culinary Knowledge Grounding,
                             Existing Culinary Precedent Analysis, Innovation Delta Quality,
                             Mechanistic Plausibility, Innovation Value)
      -> Concept Ranking / Top-K
      -> Recipe Realization (RecipeConcept + InnovationTrace -> Recipe)
      -> Stage-B CIE        (1 recipe-level dimension: Realization Quality)
      -> Final Ranking      (single six-dimension weighted total)
      -> Output

CANONICAL CONTRACT (CIE v3)
---------------------------
The `InnovationTrace` model mirrors the canonical `innovation_trace` object defined in
`CIE-Culinary-Bench/schema/cie_sample.schema.json` (the frozen benchmark). Field names, nesting
and value types are aligned; compatibility is asserted by automated tests
(`tests/test_scoring_invariants.py::test_innovation_trace_matches_canonical_sample`). The model
forbids extra fields and blank required strings so an empty array / whitespace-only field cannot
masquerade as a complete trace.

The six evaluation dimensions and their weights mirror
`CIE-Culinary-Bench/schema/scoring_rubric.json` (scale 1-5, INTEGER levels only). `EvalScore.score`
is strictly an integer 1-5: fractional, out-of-range, NaN, Infinity, boolean and garbage-string
inputs are rejected at construction time.

Historical migration note (deprecated, for readers of older commits only): before this
alignment the application used a four-field trace
(`ingredient_knowledge` / `concept_bridge` / `creative_hypothesis` /
`preliminary_feasibility_reasoning`) and a different six-dimension set
(`ingredient_intelligence` / `flavor_bridge_quality` / `creative_leap` /
`exploration_value` / `culinary_feasibility` / `communication_quality`).
Those names are no longer part of any contract; see `docs/cie_framework.md`.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Ingredient(BaseModel):
    """A raw input ingredient supplied by the user."""

    name: str = Field(..., description="Ingredient name, e.g. 'chicken'")
    quantity: Optional[str] = Field(None, description="Optional amount/unit, e.g. '200g' or '2 pcs'")
    note: Optional[str] = Field(None, description="Optional constraint note, e.g. 'prefer fresh'")


class Stage(str, Enum):
    """Which CIE stage produced a given dimension score."""

    A = "A"  # evaluated on RecipeConcept, before realization
    B = "B"  # evaluated on full Recipe, after realization


class CIEStageDimensions:
    """Two-stage split of the six canonical CIE v3 dimensions.

    Stage A scores the five *concept-level* dimensions (used for candidate ranking / Top-K).
    Stage B scores only `realization_quality`, which needs the realized Recipe.

    The authoritative default weights live in `cie/dimensions/__init__.py` (the tunable hub).
    """

    STAGE_A: tuple[str, ...] = (
        "culinary_knowledge_grounding",
        "existing_culinary_precedent_analysis",
        "innovation_delta_quality",
        "mechanistic_plausibility",
        "innovation_value",
    )
    STAGE_B: tuple[str, ...] = ("realization_quality",)
    ALL: tuple[str, ...] = STAGE_A + STAGE_B


# --- Canonical vocabularies (mirrored from the frozen benchmark corpus) -----------------
#: Observed `innovation_delta.change_type` vocabulary in the 30 frozen benchmark cases.
#: Advisory, not enforced — the canonical schema types `change_type` as an array of strings.
CHANGE_TYPE_VOCABULARY: tuple[str, ...] = (
    "ingredient substitution",
    "ingredient stacking",
    "ingredient transformation",
    "technique transfer",
    "texture transformation",
    "flavor architecture",
    "role transformation",
    "presentation",
)

#: Observed `mechanistic_justification.strength` vocabulary in the frozen benchmark corpus.
MECHANISM_STRENGTH_VALUES: tuple[str, ...] = ("weak", "medium", "strong")

#: Canonical CIE v3 score scale (see `CIE-Culinary-Bench/schema/scoring_rubric.json`).
SCORE_MIN: int = 1
SCORE_MAX: int = 5
#: Plan-level ceiling for `realization_quality` when no explicit empirical evidence is supplied.
#: The 5-level is reserved for when actual realization/verification evidence is available.
SCORE_MAX_PLAN: int = 4


class _TraceModel(BaseModel):
    """Base for canonical CIE v3 trace models.

    - `extra="forbid"` mirrors the canonical benchmark `innovation_trace` shape
      (additionalProperties: false) so extra keys cannot masquerade as a complete trace.
    - Blank required strings are rejected (a whitespace-only field is not a valid trace field).
    """

    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="after")
    @classmethod
    def _no_blank_strings(cls, v: object) -> object:
        if isinstance(v, str):
            stripped = v.strip()
            if stripped == "":
                raise ValueError("required string field must not be blank")
            return stripped
        return v


# --- Six-stage Innovation Trace (canonical CIE v3) --------------------------------------
class ExistingCulinaryContext(_TraceModel):
    """Stage 1 — what already exists that this idea departs from."""

    precedents: List[str] = Field(
        ...,
        min_length=1,
        description="Closest existing dishes / traditions / prior techniques, most specific first",
    )
    relationship: str = Field(
        ..., description="How the new idea inherits from and departs from those precedents"
    )

    @field_validator("precedents", mode="after")
    @classmethod
    def _precedents_items_non_blank(cls, v: List[str]) -> List[str]:
        out: List[str] = []
        for item in v:
            if not isinstance(item, str):
                raise ValueError(f"precedents items must be strings, got {type(item).__name__}")
            s = item.strip()
            if s == "":
                raise ValueError("precedents items must not be blank")
            out.append(s)
        return out


class IngredientKnowledgeItem(_TraceModel):
    """One ingredient and its culinary-relevant physical/flavor property."""

    ingredient: str = Field(..., description="Ingredient name")
    property: str = Field(
        ..., description="Culinary role and physical/flavor behaviour, including its limits"
    )


class TechniqueKnowledgeItem(_TraceModel):
    """One technique and the principle that makes it work."""

    technique: str = Field(..., description="Technique name")
    principle: str = Field(
        ..., description="Why the technique produces its effect, and what it does NOT do"
    )


class IngredientAndTechniqueKnowledge(_TraceModel):
    """Stage 2 — grounded ingredient and technique knowledge."""

    ingredient_knowledge: List[IngredientKnowledgeItem] = Field(
        ..., min_length=1, description="Per-ingredient knowledge with explicit boundaries"
    )
    technique_knowledge: List[TechniqueKnowledgeItem] = Field(
        ..., min_length=1, description="Per-technique knowledge with explicit boundaries"
    )


class InnovationDelta(_TraceModel):
    """Stage 3 — the concrete before -> after change."""

    before: str = Field(..., description="The prior/conventional state")
    after: str = Field(..., description="The proposed state")
    change_type: List[str] = Field(
        ...,
        min_length=1,
        description="Kinds of change involved; prefer the canonical vocabulary "
        "(see CHANGE_TYPE_VOCABULARY)",
    )
    magnitude: int = Field(
        ...,
        ge=0,
        le=5,
        description="Magnitude of the change, integer 0-5. Magnitude expresses SIZE of change only, "
        "never innovation value.",
    )

    @field_validator("change_type", mode="after")
    @classmethod
    def _change_type_items_non_blank(cls, v: List[str]) -> List[str]:
        out: List[str] = []
        for item in v:
            if not isinstance(item, str):
                raise ValueError(f"change_type items must be strings, got {type(item).__name__}")
            s = item.strip()
            if s == "":
                raise ValueError("change_type items must not be blank")
            out.append(s)
        return out


class MechanisticJustification(_TraceModel):
    """Stage 4 — why the change should work, mechanistically."""

    flavor_mechanism: str = Field(..., description="Flavor/aroma mechanism behind the change")
    texture_mechanism: str = Field(..., description="Texture/structure mechanism behind the change")
    chemical_or_culinary_basis: str = Field(
        ..., description="Chemical or established culinary basis, including what remains unproven"
    )
    strength: Literal["weak", "medium", "strong"] = Field(
        ...,
        description="Self-assessed strength of the mechanistic argument: weak | medium | strong",
    )


class RiskAndConstraint(_TraceModel):
    """Stage 6 — falsifiable risks, tradeoffs and failure conditions."""

    risk: str = Field(..., description="What is most likely to go wrong")
    tradeoff: str = Field(..., description="What is given up in exchange for the change")
    failure_condition: str = Field(
        ..., description="Observable condition under which the idea should be judged a failure"
    )


class InnovationTrace(_TraceModel):
    """Explicit, auditable six-stage innovation trajectory produced during Creative Ideation.

    Mirrors the canonical `innovation_trace` object in
    `CIE-Culinary-Bench/schema/cie_sample.schema.json`; field/type/key-constraint compatibility is
    asserted by automated tests. Do NOT describe this as "field-for-field compatible" unless those
    tests pass.

    IMPORTANT: This is a structured reasoning artifact generated by the LLM to make the
    creative process transparent and reviewable. It is NOT a claim about the model's true
    internal thought process.
    """

    existing_culinary_context: ExistingCulinaryContext = Field(
        ..., description="Stage 1 — Existing Culinary Context"
    )
    ingredient_and_technique_knowledge: IngredientAndTechniqueKnowledge = Field(
        ..., description="Stage 2 — Ingredient & Technique Knowledge"
    )
    innovation_delta: InnovationDelta = Field(..., description="Stage 3 — Innovation Delta")
    mechanistic_justification: MechanisticJustification = Field(
        ..., description="Stage 4 — Mechanistic Justification"
    )
    creative_hypothesis: str = Field(
        ..., description="Stage 5 — Creative Hypothesis: the novel idea being proposed"
    )
    risk_and_constraint: RiskAndConstraint = Field(
        ..., description="Stage 6 — Risk & Constraint"
    )


class RecipeConcept(BaseModel):
    """Creative Ideation output, grounded in an explicit six-stage InnovationTrace.

    The trace is the basis for forming this concept and for later CIE review.
    """

    concept_name: str = Field(..., description="Working name of the concept")
    ingredients: List[str] = Field(
        ..., description="Ingredient names involved in this concept (subset of the given ingredients)"
    )
    creative_angle: str = Field(..., description="What makes this concept creative")
    core_idea: str = Field(..., description="The central creative idea of the concept")
    trace: InnovationTrace = Field(
        ..., description="Explicit six-stage innovation trajectory that produced this concept"
    )


class Recipe(BaseModel):
    """A fully realized recipe produced by Recipe Realization."""

    name: str = Field(..., description="Final dish name")
    ingredients: List[Ingredient] = Field(..., description="Required (hero) ingredients")
    seasonings: List[Ingredient] = Field(
        default_factory=list,
        description="Seasonings / condiments (e.g. salt, pepper, spices) — kept separate from hero ingredients",
    )
    steps: List[str] = Field(..., description="Ordered cooking steps")
    creative_explanation: str = Field(..., description="Human-readable explanation of the creativity")
    creative_hypothesis: Optional[str] = Field(
        None,
        description="The ORIGINAL creative hypothesis carried from the concept's InnovationTrace "
        "(stage 5). Realization must preserve it and must NOT re-invent the creative point.",
    )
    concept_name: Optional[str] = Field(
        None, description="Source concept name, for traceability back to its InnovationTrace"
    )


class EvalScore(BaseModel):
    """A single CIE dimension score on the canonical 1-5 INTEGER scale.

    `score` is strictly an integer in [SCORE_MIN, SCORE_MAX]. The `field_validator` below rejects
    fractional values (4.5), out-of-range integers (0, 6), NaN, Infinity, booleans and non-numeric
    strings — Pydantic's lax float->int coercion is intentionally NOT relied upon alone, it is
    re-asserted explicitly and proven by tests.
    """

    dimension: str = Field(..., description="Dimension key, e.g. 'innovation_delta_quality'")
    stage: Stage = Field(..., description="Which CIE stage evaluated this dimension")
    score: int = Field(
        ...,
        ge=SCORE_MIN,
        le=SCORE_MAX,
        description="Score on the canonical CIE v3 1-5 integer scale (no fractional levels)",
    )
    reason: str = Field(..., description="One-line justification for the score")

    @field_validator("score", mode="before")
    @classmethod
    def _enforce_integer_score(cls, v: object) -> int:
        if isinstance(v, bool):  # bool is a subclass of int — treat as invalid
            raise ValueError("score must be an integer 1-5, not a bool")
        if isinstance(v, float):
            if not v.is_integer():
                raise ValueError(f"score must be a whole integer level, got fractional {v!r}")
            v = int(v)
        if not isinstance(v, int):
            raise ValueError(f"score must be an integer 1-5, got {type(v).__name__}: {v!r}")
        if v < SCORE_MIN or v > SCORE_MAX:
            raise ValueError(f"score must be between {SCORE_MIN} and {SCORE_MAX}, got {v}")
        return v


class ConceptEval(BaseModel):
    """Stage-A evaluation result for one RecipeConcept (5 concept-level dimensions)."""

    concept_name: str
    scores: List[EvalScore]  # Stage A dimensions
    trace: InnovationTrace


class RecipeEval(BaseModel):
    """Stage-B evaluation result for one realized Recipe (realization_quality only)."""

    recipe_name: str
    concept_name: Optional[str] = None
    scores: List[EvalScore]  # Stage B dimensions


class EvalReport(BaseModel):
    """Final combined six-dimension report for one candidate.

    The final total is the CANONICAL CIE v3 aggregation — a single direct weighted sum over
    all six dimensions:

        total_score = sum(WEIGHTS[d] * score[d] for d in ALL_SIX_DIMENSIONS)

    with WEIGHTS = 0.15 / 0.15 / 0.25 / 0.20 / 0.15 / 0.10 summing to 1.0.

    `stage_a_score` and `stage_b_score` are DIAGNOSTIC sub-aggregates only (they exist so
    Stage-A candidates can be ranked before realization). They are NOT inputs to
    `total_score`; there is no stage-level blend such as the historical 0.75 / 0.25.
    """

    concept_name: str
    trace: InnovationTrace
    stage_a: List[EvalScore]
    stage_b: List[EvalScore]
    stage_a_score: float = Field(
        0.0,
        description="DIAGNOSTIC: weights-normalized average of the five Stage-A dimensions (1-5)",
    )
    stage_b_score: float = Field(
        0.0,
        description="DIAGNOSTIC: weights-normalized average of the Stage-B dimension(s) (1-5)",
    )
    total_score: float = Field(
        ..., description="Canonical six-dimension direct weighted sum, sum(w_d * score_d) (1-5)"
    )
    rank: int = Field(..., description="Final rank among candidates (1 = best)")


class PipelineResult(BaseModel):
    """Final pipeline output delivered to the caller / CLI."""

    inputs: List[Ingredient] = Field(default_factory=list, description="Original input ingredients")
    concepts: List[RecipeConcept] = Field(default_factory=list, description="All generated concepts")
    recipes: List[Recipe] = Field(default_factory=list, description="Realized recipes (top concepts)")
    reports: List[EvalReport] = Field(default_factory=list, description="Final six-dimension reports")
    best_recipe: Optional[Recipe] = Field(None, description="Chosen best recipe (Top-1)")
    best_report: Optional[EvalReport] = Field(None, description="Report for the best recipe")
