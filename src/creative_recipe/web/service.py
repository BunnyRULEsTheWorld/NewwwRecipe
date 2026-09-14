"""Thin service adapter: transport models <-> the existing NewwwRecipe pipeline.

Deliberately contains NO recipe-generation and NO scoring logic. It:

1. turns a `GenerateRequest` into the inputs the existing pipeline already expects
   (`List[Ingredient]` + a single human-readable `constraints` string),
2. runs `creative_recipe.pipeline.run(...)` unchanged,
3. maps the canonical `PipelineResult` onto the API response models.

Preferences are propagated, not dropped: they are rendered into the pipeline's existing
`constraints` input (the least invasive compatible way — no domain signature changes).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..cie.dimensions import WEIGHTS as DIMENSION_WEIGHTS
from ..config import Config
from ..llm.base import LLMProvider
from ..llm.fake import DemoProvider
from ..llm.hy3 import Hy3LLMClient
from ..pipeline import run as run_pipeline
from ..types import Ingredient, PipelineResult, Recipe
from . import ingredient_catalog as catalog
from .models import (
    CiePayload,
    ConceptPayload,
    DIMENSION_EXPLANATIONS,
    DIMENSION_LABELS,
    DimensionScore,
    GenerateRequest,
    GenerateResponse,
    GenerationMeta,
    RecipeIngredient,
    RecipePayload,
    TRACE_STAGE_KEYS,
    TRACE_STAGE_LABELS,
    TRACE_STAGE_SUMMARIES,
    TracePayload,
    TraceStage,
)

#: Pipeline knobs for interactive use (kept small so a single request stays responsive).
NUM_CONCEPTS = 3
TOP_K_CONCEPTS = 1
TOP_K_FINAL = 1


class GenerationUnavailable(RuntimeError):
    """Raised when a real (non-demo) generation is requested but cannot be performed."""


# --- Preferences -> pipeline constraints -----------------------------------------------------
def build_constraints(preferences: Any, avoid: Optional[List[str]] = None) -> str:
    """Render preferences + repetition hints into the pipeline's existing `constraints` input.

    The pipeline already threads `constraints` into Creative Ideation, Recipe Realization and the
    CIE judge context, so rendering them here reaches every stage without touching domain code.
    """
    lines: List[str] = list(preferences.to_display_lines())
    free_text = (getattr(preferences, "constraints", None) or "").strip()
    if free_text:
        lines.append(f"Additional constraints: {free_text}")
    avoid_titles = [t.strip() for t in (avoid or []) if t and t.strip()]
    if avoid_titles:
        lines.append(
            "Do NOT repeat or lightly reword these already-shown recipes: "
            + "; ".join(avoid_titles)
        )
    return "\n".join(lines)


def build_ingredients(ingredient_ids: List[str]) -> List[Ingredient]:
    """Catalog ids -> domain `Ingredient` objects, preserving order and removing duplicates."""
    seen: set[str] = set()
    out: List[Ingredient] = []
    for raw in ingredient_ids:
        key = (raw or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(Ingredient(name=catalog.display_name(key)))
    return out


# --- Provider resolution --------------------------------------------------------------------
def resolve_provider(force_demo: Optional[bool] = None) -> Tuple[LLMProvider, str, str, bool]:
    """Return (provider, provider_name, model_name, demo_mode).

    Demo mode is the repository's legitimate offline path (`DemoProvider`): it is used
    automatically when no `HY3_API_KEY` is configured, and can be forced either way by the
    request. Requesting the real provider without credentials is an error, never a silent
    fallback to invented data.
    """
    cfg = Config.from_env(require_key=False)
    has_key = bool(cfg.hy3_api_key)
    demo_mode = (not has_key) if force_demo is None else bool(force_demo)

    if demo_mode:
        return DemoProvider(), "demo", "demo-offline", True
    if not has_key:
        raise GenerationUnavailable(
            "HY3_API_KEY is not configured, so the real provider cannot be used. "
            "Copy .env.example to .env and set HY3_API_KEY, or run in demo mode."
        )
    return Hy3LLMClient.from_config(cfg), "hy3", cfg.hy3_model, False


# --- Mapping --------------------------------------------------------------------------------
def _ingredient_payload(items: List[Ingredient]) -> List[RecipeIngredient]:
    return [
        RecipeIngredient(name=i.name, quantity=i.quantity, note=i.note)
        for i in items
    ]


def _recipe_payload(recipe: Recipe) -> RecipePayload:
    return RecipePayload(
        name=recipe.name,
        ingredients=_ingredient_payload(recipe.ingredients),
        seasonings=_ingredient_payload(recipe.seasonings),
        steps=list(recipe.steps),
        creative_explanation=recipe.creative_explanation,
        creative_hypothesis=recipe.creative_hypothesis,
        concept_name=recipe.concept_name,
        # servings / estimated_time / difficulty are NOT produced by the current backend and are
        # therefore left unset rather than invented.
        servings=None,
        estimated_time=None,
        difficulty=None,
    )


def _trace_payload(trace: Any) -> TracePayload:
    raw: Dict[str, Any] = trace.model_dump() if hasattr(trace, "model_dump") else dict(trace)
    stages: List[TraceStage] = []
    for index, key in enumerate(TRACE_STAGE_KEYS, start=1):
        if key not in raw:
            continue
        content = raw[key]
        if isinstance(content, str):
            content = {"text": content}
        stages.append(
            TraceStage(
                key=key,
                index=index,
                label=TRACE_STAGE_LABELS[key],
                summary=TRACE_STAGE_SUMMARIES[key],
                content=content,
            )
        )
    risk = raw.get("risk_and_constraint") or {}
    risk_notes: Optional[str] = None
    if isinstance(risk, dict):
        parts = [
            f"Risk: {risk.get('risk', '')}".strip(),
            f"Tradeoff: {risk.get('tradeoff', '')}".strip(),
            f"Failure condition: {risk.get('failure_condition', '')}".strip(),
        ]
        risk_notes = " ".join(p for p in parts if p and not p.endswith(": "))
    return TracePayload(
        stages=stages,
        creative_hypothesis=raw.get("creative_hypothesis"),
        risk_notes=risk_notes,
    )


def _cie_payload(report: Any) -> CiePayload:
    """Map the canonical EvalReport: six dimensions, exactly once each, integer 1-5.

    `total_score` is taken verbatim from the backend (direct six-dimension weighted sum).
    """
    scores = list(report.stage_a) + list(report.stage_b)
    by_key: Dict[str, Any] = {}
    for s in scores:
        by_key.setdefault(s.dimension, s)

    dimensions: List[DimensionScore] = []
    for key in report_rank_order():
        if key not in by_key:
            continue
        s = by_key[key]
        dimensions.append(
            DimensionScore(
                key=key,
                label=DIMENSION_LABELS.get(key, key),
                weight=DIMENSION_WEIGHTS[key],
                score=int(s.score),
                reason=s.reason,
                stage=s.stage.value,
                explanation=DIMENSION_EXPLANATIONS.get(key, ""),
            )
        )
    return CiePayload(
        total_score=float(report.total_score),
        dimensions=dimensions,
        stage_a_score=float(getattr(report, "stage_a_score", 0.0) or 0.0),
        stage_b_score=float(getattr(report, "stage_b_score", 0.0) or 0.0),
    )


def report_rank_order() -> List[str]:
    """Canonical (weight-descending) display order of the six dimensions."""
    return sorted(DIMENSION_WEIGHTS, key=lambda k: (-DIMENSION_WEIGHTS[k], k))


def generate(req: GenerateRequest) -> GenerateResponse:
    """Run the existing pipeline and map the canonical result.

    Raises `GenerationUnavailable` for configuration problems and lets genuine pipeline/LLM
    errors propagate (the API layer turns them into a real error response — never a fake recipe).
    """
    provider, provider_name, model_name, demo_mode = resolve_provider(req.demo)
    ingredients = build_ingredients(req.ingredients)
    constraints = build_constraints(req.preferences, req.avoid)

    fallback_reason: Optional[str] = None
    try:
        result: PipelineResult = run_pipeline(
            provider,
            ingredients,
            constraints=constraints,
            num_concepts=NUM_CONCEPTS,
            top_k_concepts=TOP_K_CONCEPTS,
            top_k_final=TOP_K_FINAL,
        )
    except Exception as exc:  # Real (Hy3) attempt failed — fall back, never fake success.
        if not demo_mode:
            provider, provider_name, model_name, demo_mode = (
                DemoProvider(),
                "demo",
                "demo-fallback",
                True,
            )
            fallback_reason = (
                f"Live generation failed ({type(exc).__name__}: {exc}); "
                "fell back to the offline DemoProvider."
            )
            result = run_pipeline(
                provider,
                ingredients,
                constraints=constraints,
                num_concepts=NUM_CONCEPTS,
                top_k_concepts=TOP_K_CONCEPTS,
                top_k_final=TOP_K_FINAL,
            )
        else:
            raise

    recipe: Optional[Recipe] = result.best_recipe
    if recipe is None:
        raise GenerationUnavailable(
            "The pipeline produced no recipe for these ingredients. Please adjust your "
            "selection or preferences and try again."
        )

    concept_payload: Optional[ConceptPayload] = None
    if recipe.concept_name:
        src = next((c for c in result.concepts if c.concept_name == recipe.concept_name), None)
        if src is not None:
            concept_payload = ConceptPayload(
                name=src.concept_name,
                ingredients=list(src.ingredients),
                creative_angle=src.creative_angle,
                core_idea=src.core_idea,
            )

    trace_payload: Optional[TracePayload] = None
    cie_payload: Optional[CiePayload] = None
    rank: Optional[int] = None
    if result.best_report is not None:
        trace_payload = _trace_payload(result.best_report.trace)
        cie_payload = _cie_payload(result.best_report)
        rank = result.best_report.rank

    return GenerateResponse(
        recipe=_recipe_payload(recipe),
        concept=concept_payload,
        trace=trace_payload,
        cie=cie_payload,
        meta=GenerationMeta(
            provider=provider_name,
            demo_mode=demo_mode,
            model=model_name,
            requested_ingredients=list(req.ingredients),
            requested_preferences=req.preferences,
            concept_count=len(result.concepts),
            recipe_count=len(result.recipes),
            rank=rank,
            fallback_reason=fallback_reason,
        ),
    )
