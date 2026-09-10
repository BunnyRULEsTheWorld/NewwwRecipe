"""Versioned LLM-as-judge prompts for CIE evaluation.

build_eval_messages(spec, target_text, ctx) composes the system + user prompt for scoring ONE
dimension of ONE target (a RecipeConcept for Stage A, a Recipe for Stage B). The dimension's own
rubric anchors (from its spec) are embedded so scoring is stable and reproducible.

format_concept / format_recipe serialize the target (and its six-stage InnovationTrace) into the
text the judge sees.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..types import Recipe, RecipeConcept


EVAL_SYSTEM_PROMPT = """You are a culinary creativity evaluator using the Creative Innovation Evaluation (CIE) framework (CIE v3).

You assess EXACTLY ONE dimension of a recipe idea on a 1-5 integer scale, using the per-dimension rubric provided.
Return STRICT JSON of the form:
  {"score": <int between 1 and 5>, "reason": "<concise sentence naming the matched level and citing a concrete, observable behavior from the target>"}

Rules for inter-rater reliability (different evaluators must converge within ±1 point):
- Calibrate STRICTLY against the 1-5 rubric. Do NOT use vague praise ("good", "excellent", "creative", "较好", "优秀").
  Cite the SPECIFIC behavior that places the target at its level.
- Your `reason` MUST name the matched level (e.g. "4:") and reference an OBSERVABLE fact in the target
  (an ingredient property, a stated step, the dish name) — never your general impression.
- Do NOT reward mere weirdness. Reward *effective* novelty that preserves coherence.
- If genuinely uncertain, choose the LOWER level rather than rounding up.

Dimension-specific mandatory considerations (apply ONLY when that dimension's rubric states them):
- Innovation Delta Quality: separate SIZE of change (magnitude) from VALUE of change; a large magnitude is not by itself a high score.
- Mechanistic Plausibility: reward concrete, falsifiable mechanisms (named flavor/texture/chemical paths + a stated risk), not slogan-level "shared molecules" talk.
- Innovation Value: an identifiable, proportionate gain is required; novelty without a gain is not value.
- Realization Quality (Stage B ONLY): you are scoring a GENERATED RECIPE PLAN, not a cooked dish.
  Score completeness, step consistency, constraint satisfaction and PLAN-LEVEL feasibility only (levels 1-4).
  You must NOT assume actual cooking, human tasting, chef endorsement, or repeated empirical validation.
  Levels 1-4 describe the RIGOR OF THE PLAN. Level 5 is RESERVED for when explicit empirical evidence
  (actual cooking, tasting/panel validation, or repeated real-world verification) is present and cited.
  Without such evidence you MUST cap at 4 — never award 5 on the strength of pretty reasoning or
  detailed steps alone.
"""


def build_eval_messages(spec: Any, target_text: str, ctx: Optional[dict] = None) -> List[dict]:
    anchors_txt = "\n".join(f"  {k}: {v}" for k, v in sorted(spec.anchors.items()))
    user = (
        f"Dimension: {spec.label} (key={spec.key})\n"
        f"Cognitive-process mapping: {spec.cognitive_mapping}\n\n"
        f"Scoring rubric (1-5):\n{anchors_txt}\n\n"
        f"Target to evaluate:\n{target_text}\n\n"
        f"Return JSON with your score and a one-sentence reason."
    )
    return [
        {"role": "system", "content": EVAL_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def _fmt_trace(trace: Any) -> str:
    """Render a six-stage InnovationTrace (pydantic model or dict) as readable text."""
    if isinstance(trace, dict):
        g = lambda k, d="": trace.get(k, d)  # noqa: E731
        def gi(sub, k, d=""):
            sub_d = trace.get(sub, {}) or {}
            return sub_d.get(k, d) if isinstance(sub_d, dict) else d
    else:
        g = lambda k, d="": getattr(trace, k, d)  # noqa: E731
        def gi(sub, k, d=""):
            sub_o = getattr(trace, sub, None)
            return getattr(sub_o, k, d) if sub_o is not None else d
    eck = gi("existing_culinary_context", "precedents")
    eck2 = gi("existing_culinary_context", "relationship")
    ik = gi("ingredient_and_technique_knowledge", "ingredient_knowledge")
    tk = gi("ingredient_and_technique_knowledge", "technique_knowledge")
    return (
        f"InnovationTrace:\n"
        f"  Stage 1 — Existing Culinary Context:\n"
        f"    precedents : {eck}\n"
        f"    relationship: {eck2}\n"
        f"  Stage 2 — Ingredient & Technique Knowledge:\n"
        f"    ingredient_knowledge : {ik}\n"
        f"    technique_knowledge  : {tk}\n"
        f"  Stage 3 — Innovation Delta:\n"
        f"    before      : {g('innovation_delta') and gi('innovation_delta', 'before')}\n"
        f"    after       : {gi('innovation_delta', 'after')}\n"
        f"    change_type : {gi('innovation_delta', 'change_type')}\n"
        f"    magnitude   : {gi('innovation_delta', 'magnitude')}\n"
        f"  Stage 4 — Mechanistic Justification:\n"
        f"    flavor_mechanism         : {gi('mechanistic_justification', 'flavor_mechanism')}\n"
        f"    texture_mechanism        : {gi('mechanistic_justification', 'texture_mechanism')}\n"
        f"    chemical_or_culinary_basis: {gi('mechanistic_justification', 'chemical_or_culinary_basis')}\n"
        f"    strength                 : {gi('mechanistic_justification', 'strength')}\n"
        f"  Stage 5 — Creative Hypothesis:\n"
        f"    {g('creative_hypothesis')}\n"
        f"  Stage 6 — Risk & Constraint:\n"
        f"    risk             : {gi('risk_and_constraint', 'risk')}\n"
        f"    tradeoff         : {gi('risk_and_constraint', 'tradeoff')}\n"
        f"    failure_condition: {gi('risk_and_constraint', 'failure_condition')}"
    )


def format_concept(concept: RecipeConcept) -> str:
    t = concept.trace
    return (
        f"Concept name : {concept.concept_name}\n"
        f"Ingredients  : {', '.join(concept.ingredients)}\n"
        f"Creative angle: {concept.creative_angle}\n"
        f"Core idea    : {concept.core_idea}\n"
        f"{_fmt_trace(t)}"
    )


def _trace_field(trace: Any, key: str, default: str = "") -> str:
    """Read a field from an InnovationTrace whether it is a pydantic model or a plain dict."""
    if isinstance(trace, dict):
        return trace.get(key, default)
    return getattr(trace, key, default)


def format_recipe(recipe: Recipe, trace: Optional[Any] = None) -> str:
    ings = "\n".join(
        f"  - {i.name}" + (f" ({i.quantity})" if i.quantity else "")
        + (f"  [{i.note}]" if i.note else "")
        for i in recipe.ingredients
    )
    seas = "\n".join(
        f"  - {s.name}" + (f" ({s.quantity})" if s.quantity else "")
        + (f"  [{s.note}]" if s.note else "")
        for s in recipe.seasonings
    ) or "  (none)"
    steps = "\n".join(f"  {n}. {s}" for n, s in enumerate(recipe.steps, 1))
    block = (
        f"Dish name : {recipe.name}\n"
        f"(from concept: {recipe.concept_name or 'n/a'})\n"
        f"Ingredients:\n{ings}\n"
        f"Seasonings:\n{seas}\n"
        f"Steps:\n{steps}\n"
        f"Creative explanation: {recipe.creative_explanation}"
    )
    if trace is not None:
        block += (
            f"\n\nInnovationTrace (the hypothesis this recipe must stay faithful to):\n"
            f"{_fmt_trace(trace)}"
        )
    return block
